from typing import List, Dict, Tuple, TypedDict, Union, Any
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger
from collections import defaultdict
from ebl.atf_importer.domain.line_context import LineContext


class QueryArgs(TypedDict, total=False):
    lemma_field: str
    lemma_value: Union[str, List[str]]
    guideword_field: str = ""
    guideword_value: str = ""


class LemmaLookup:
    def __init__(
        self, database, config: AtfImporterConfigData, logger: Logger, glossary_data
    ):
        self.database = database
        self.config = config
        self.logger = logger
        self.glossary_data = glossary_data

    def lookup_lemma(self, lemma: str, guideword: str, pos_tag: str) -> List[Dict]:
        if lemma in {"X", "u", "n"}:
            self.logger.warning(f"No lemmatization: Blank Oracc lemma '{lemma}'")
            return []
        lemma = lemma.strip()
        guideword = self._clean_guideword(guideword)
        unique_lemmas = self._get_unique_lemmas(lemma, guideword, pos_tag)
        self._log_warning_if_no_lemmas(unique_lemmas, lemma, guideword)
        return [{"_id": lemma_id} for lemma_id in unique_lemmas]

    def _get_unique_lemmas(self, lemma: str, guideword: str, pos_tag: str) -> List[str]:
        if lemma.startswith("+"):
            return self._lookup_prefixed_lemma(lemma[1:], guideword)
        else:
            unique_lemmas = self._lookup_standard_lemma(lemma, guideword, pos_tag)
            if not unique_lemmas and pos_tag in self.config["NOUN_POS_TAGS"]:
                return self._query_database(
                    {"lemma_field": "oraccWords.lemma", "lemma_value": lemma}
                )
            return unique_lemmas

    def _log_warning_if_no_lemmas(
        self, unique_lemmas: List[str], lemma: str, guideword: str
    ) -> None:
        if not unique_lemmas:
            self.logger.warning(
                "Incompatible lemmatization: No eBL word found for lemma"
                f" '{lemma}' and guide word '{guideword}'",
                "not_lemmatized_tokens",
            )

    def _clean_guideword(self, guideword: str) -> str:
        guideword = guideword.strip().strip("[]")
        return guideword.split("//")[0] if "//" in guideword else guideword

    def _lookup_prefixed_lemma(self, lemma: str, guideword: str) -> List[str]:
        lemma = lemma.replace("ʾ", "'")
        unique_lemmas = self._query_database(
            {
                "lemma_field": "oraccWords.lemma",
                "lemma_value": lemma,
                "guideword_field": "oraccWords.guideWord",
                "guideword_value": guideword,
            }
        ) or self._query_multiple_sources(lemma, guideword)

        return unique_lemmas

    def _lookup_standard_lemma(
        self, lemma: str, guideword: str, pos_tag: str
    ) -> List[str]:
        try:
            citation_form, guideword = self.glossary_data["lemposgw_cfgw"][
                lemma + pos_tag + guideword
            ]
            guideword = self._clean_guideword(guideword)
            unique_lemmas = self._query_sources(citation_form, guideword)
            return unique_lemmas
        except KeyError:
            self.logger.warning(
                "Incompatible lemmatization: No citation form"
                f" or guideword (by sense) found in the glossary for '{lemma}'",
                "not_lemmatized_tokens",
            )
            return []

        return unique_lemmas

    def _query_sources(
        self, lemma: str, guideword: str, citation_form: str
    ) -> List[str]:
        lemma_guideword_pairs = [
            ("forms.lemma", "guideWord", [lemma]),
            ("lemma", "guideWord", [lemma]),
            ("oraccWords.lemma", "oraccWords.guideWord", citation_form),
        ]
        unique_lemmas = []
        for lemma_field, guideword_field, lemma_value in lemma_guideword_pairs:
            unique_lemmas += self._query_database(
                {
                    "lemma_field": lemma_field,
                    "lemma_value": lemma_value,
                    "guideword_field": guideword_field,
                    "guideword_value": guideword,
                }
            )
        print("query_multiple_sources", unique_lemmas)
        return unique_lemmas

    def _query_database(self, args: Dict[str, Any]) -> List[str]:
        query = self._build_query(args)
        print("query_database", self._execute_query(query))
        return self._execute_query(query)

    def _build_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = {args["lemma_field"]: args["lemma_value"]}
        if self._has_guideword(args):
            query[args["guideword_field"]] = args["guideword_value"]
        return query

    def _has_guideword(self, args: Dict[str, Any]) -> bool:
        return (
            "guideword_field" in args
            and "guideword_value" in args
            and args["guideword_field"]
            and args["guideword_value"]
        )

    def _execute_query(self, query: Dict[str, Any]) -> List[str]:
        aggregation_pipeline = [{"$match": query}, {"$project": {"_id": 1}}]
        return [
            entry["_id"]
            for entry in self.database.get_collection("words").aggregate(
                aggregation_pipeline
            )
        ]


class LemmaLineHandler:
    def __init__(
        self, database, config: AtfImporterConfigData, logger: Logger, glossary_data
    ):
        self.lemma_lookup = LemmaLookup(database, config, logger, glossary_data)
        self.logger = logger

    def handle_lem_line(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        context: LineContext,
    ) -> defaultdict:
        # ToDo: Check this out
        """
        if not context.last_transliteration:
            self.logger.warning(
                f"Lemmatization line without preceding text line in {filename}"
            )
            return result
        """
        all_unique_lemmas = self._get_all_unique_lemmas(line, filename, context)
        result["all_unique_lemmas"] += all_unique_lemmas
        result["last_transliteration"] = context.last_transliteration
        lemma_line = self._create_lemma_line(
            context.last_transliteration,
            all_unique_lemmas,
            context.last_transliteration_line,
        )
        result["lemmatization"].append(tuple(lemma_line))
        self._log_line(filename, context)
        return result

    def _get_all_unique_lemmas(
        self,
        line: Dict[str, Any],
        filename: str,
        context: LineContext,
    ) -> List:
        all_unique_lemmas = []
        for oracc_lemma_tupel in line["c_array"]:
            all_unique_lemmas = self._get_ebl_lemmas(
                oracc_lemma_tupel[0], all_unique_lemmas, filename
            )
        return self._add_placeholders_to_lemmas(
            all_unique_lemmas, context.last_alter_lem_line_at
        )

    def _add_placeholders_to_lemmas(
        self, all_unique_lemmas: List, last_alter_lem_line_at: List[int]
    ):
        for alter_pos in last_alter_lem_line_at:
            self.logger.warning(
                f"Adding placeholder to lemma line at position:{str(alter_pos)}"
            )
            all_unique_lemmas.insert(alter_pos, [])
        return all_unique_lemmas

    def _get_ebl_lemmas(
        self,
        oracc_lemma_tupel: Tuple[str, str, str],
        all_unique_lemmas: List,
        filename: str,
    ) -> List:
        # ToDo: Clean up
        print("oracc_lemma_tupel:", oracc_lemma_tupel)
        input()
        lemma, guideword, pos_tag = oracc_lemma_tupel
        db_entries = self._lookup_lemma(lemma, guideword, pos_tag)
        if db_entries:
            all_unique_lemmas.extend(db_entries)
        else:
            self.logger.warning(f"Lemma not found: {lemma} in {filename}")
        return all_unique_lemmas

    def _lookup_lemma(self, lemma: str, guideword: str, pos_tag: str):
        return self.lemma_lookup.lookup_lemma(lemma, guideword, pos_tag)

    def _create_lemma_line(
        self,
        last_transliteration: List[str],
        all_unique_lemmas: List,
        last_transliteration_line: str,
    ) -> List:
        if len(last_transliteration) != len(all_unique_lemmas):
            self._log_transliteration_error(last_transliteration_line)
            return []

        oracc_word_ebl_lemmas = self._map_lemmas_to_indices(
            last_transliteration, all_unique_lemmas
        )
        print(
            "\noracc_word_ebl_lemmas:",
            oracc_word_ebl_lemmas,
            "\noracc_word_ebl_lemmas:",
            all_unique_lemmas,
        )
        # ToDo:
        # Use this:
        # last_transliteration.update_lemmatization(oracc_word_ebl_lemmas)
        return last_transliteration

        # ToDo: Remove:
        # return self._generate_lemma_line(
        #    last_transliteration_line, oracc_word_ebl_lemmas
        # )

    def _log_transliteration_error(self, last_transliteration_line: str) -> None:
        self.logger.error(
            "Transliteration and Lemmatization don't have equal length:"
            f"\n{str(last_transliteration_line)}",
            "error_lines",
        )

    def _map_lemmas_to_indices(
        self, last_transliteration: List[str], all_unique_lemmas: List
    ) -> dict:
        oracc_word_ebl_lemmas = {}
        for index in range(len(last_transliteration)):
            oracc_word_ebl_lemmas[index] = all_unique_lemmas[index]
        return oracc_word_ebl_lemmas

    # ToDo: Clean up
    """
    def _generate_lemma_line(
        self, last_transliteration_line: str, oracc_word_ebl_lemmas: dict
    ) -> List:
        return []
        # ToDo: Continue from here (latest!!!!): check! this might be an issue
        # ToDo: Ideally, remove this method
        # Implement a check for lemmatization lines
        #
        # ebl_lines = parse_atf_lark(
        #    last_transliteration_line
        # )
        # lemma_line = []
        # word_count = 0
        # for token in last_transliteration_line:  # ebl_lines.lines[0].content:
        #    unique_lemma = oracc_word_ebl_lemmas.get(word_count, [])
        #    if unique_lemma:
        #        lemma_line.append(LemmatizationToken(token.value, tuple(unique_lemma)))
        #        word_count += 1
        #    else:
        #        lemma_line.append(LemmatizationToken(token.value, None))
        # return lemma_line
    """

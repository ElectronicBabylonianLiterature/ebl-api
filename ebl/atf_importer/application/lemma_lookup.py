from typing import List, Dict, TypedDict, Union, Any
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger


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
            unique_lemmas = self._query_database(
                {
                    "lemma_field": "oraccWords.lemma",
                    "lemma_value": citation_form,
                    "guideword_field": "oraccWords.guideWord",
                    "guideword_value": guideword,
                }
            ) or self._query_multiple_sources(citation_form, guideword)
        except KeyError:
            self.logger.warning(
                "Incompatible lemmatization: No citation form"
                f" or guideword (by sense) found in the glossary for '{lemma}'",
                "not_lemmatized_tokens",
            )
            return []

        return unique_lemmas

    def _query_multiple_sources(self, lemma: str, guideword: str) -> List[str]:
        sources = ["forms.lemma", "lemma"]
        unique_lemmas = []
        for source in sources:
            unique_lemmas += self._query_database(
                {
                    "lemma_field": source,
                    "lemma_value": [lemma],
                    "guideword_field": "guideWord",
                    "guideword_value": guideword,
                }
            )
        return unique_lemmas

    def _query_database(self, args: Dict[str, Any]) -> List[str]:
        query = self._build_query(args)
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

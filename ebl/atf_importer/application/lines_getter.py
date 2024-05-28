from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass
from ebl.atf_importer.application.lemma_lookup import LemmaLookup
from ebl.atf_importer.application.glossary_parser import GlossaryParserData
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.lemmatization.domain.lemmatization import LemmatizationToken


@dataclass
class LineContext:
    last_transliteration: List[str]
    last_transliteration_line: str
    last_alter_lemline_at: List[int]


class EblLinesGetter:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger,
        glossary_data: GlossaryParserData,
        test_lemmas: Optional[List] = None,
    ):
        self.logger = logger
        self.lemmalookup = LemmaLookup(database, config, logger, glossary_data)
        self.test_lemmas = test_lemmas

    def convert_to_ebl_lines(
        self,
        converted_lines: List[Dict[str, Any]],
        filename: str,
    ) -> Dict[str, List]:
        context = LineContext(
            last_transliteration=[],
            last_transliteration_line="",
            last_alter_lemline_at=[],
        )
        result = defaultdict(list)
        result["all_unique_lemmas"] = []
        for line in converted_lines:
            result, context = self._handle_line_type(line, result, filename, context)
        return dict(result)

    def _handle_line_type(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        context: LineContext,
    ) -> Tuple[defaultdict, LineContext]:
        c_type = line["c_type"]
        if c_type == "control_line":
            result = self._handle_control_line(line, result)
        elif c_type == "text_line":
            context = self._handle_text_line(line, result, context)
        elif c_type == "lem_line":
            result = self._handle_lem_line(line, result, filename, context)
        else:
            result["transliteration"].append(line["c_line"])
            result["lemmatization"].append(line["c_line"])
        return result, context

    def _handle_control_line(
        self, line: Dict[str, Any], result: defaultdict
    ) -> defaultdict:
        result["control_lines"].append(line)
        return result

    def _handle_text_line(
        self, line: Dict[str, Any], result: defaultdict, context: LineContext
    ) -> LineContext:
        context.last_transliteration = [
            entry for entry in line["c_array"] if entry != "DIŠ"
        ]
        context.last_transliteration_line = line["c_line"]
        context.last_alter_lemline_at = line["c_alter_lemline_at"]
        result["transliteration"].append(context.last_transliteration_line)
        return context

    def _handle_lem_line(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        context: LineContext,
    ) -> defaultdict:
        if not context.last_transliteration:
            self.logger.warning(
                f"Lemmatization line without preceding text line in {filename}"
            )
            return result

        all_unique_lemmas = self._get_all_unique_lemmas(line, filename)
        self._add_placeholders_to_lemmas(
            all_unique_lemmas, context.last_alter_lemline_at
        )
        result["all_unique_lemmas"] += all_unique_lemmas
        result["last_transliteration"] = context.last_transliteration
        lemma_line = self._create_lemma_line(
            context.last_transliteration,
            all_unique_lemmas,
            context.last_transliteration_line,
        )
        result["lemmatization"].append(tuple(lemma_line))
        return result

    def _get_all_unique_lemmas(
        self,
        line: Dict[str, Any],
        filename: str,
    ) -> List:
        if self.test_lemmas:
            return self.test_lemmas
        all_unique_lemmas = []
        for oracc_lemma_tupel in line["c_array"]:
            all_unique_lemmas = self._get_ebl_lemmata(
                oracc_lemma_tupel, all_unique_lemmas, filename
            )
        return all_unique_lemmas

    def _add_placeholders_to_lemmas(
        self, all_unique_lemmas: List, last_alter_lemline_at: List[int]
    ):
        for alter_pos in last_alter_lemline_at:
            self.logger.warning(
                f"Adding placeholder to lemma line at position:{str(alter_pos)}"
            )
            all_unique_lemmas.insert(alter_pos, [])

    def _get_ebl_lemmata(
        self,
        oracc_lemma_tupel: Tuple[str, str, str],
        all_unique_lemmas: List,
        filename: str,
    ) -> List:
        lemma, guideword, pos_tag = oracc_lemma_tupel
        db_entries = self._lookup_lemma(lemma, guideword, pos_tag)
        if db_entries:
            all_unique_lemmas.extend(db_entries)
        else:
            self.logger.warning(f"Lemma not found: {lemma} in {filename}")
        return all_unique_lemmas

    def _lookup_lemma(self, lemma: str, guideword: str, pos_tag: str):
        return self.lemmalookup.lookup_lemma(lemma, guideword, pos_tag)

    def _create_lemma_line(
        self,
        last_transliteration: List[str],
        all_unique_lemmas: List,
        last_transliteration_line: str,
    ) -> List:
        oracc_word_ebl_lemmas = {}
        if len(last_transliteration) != len(all_unique_lemmas):
            self.logger.error(
                "Transliteration and Lemmatization don't have equal length!!"
            )
            self.logger.error_lines.append(
                f"Transliteration {str(last_transliteration_line)}"
            )

        for index, oracc_word in enumerate(last_transliteration):
            # ToDo: Check if `oracc_word` should go somewhere.
            #
            # ebl/atf_importer/application/lines_getter.py:165:18:
            # B007 Loop control variable 'oracc_word' not used within the loop body.
            # If this is intended, start the name with an underscore..
            oracc_word_ebl_lemmas[index] = all_unique_lemmas[index]

        ebl_lines = parse_atf_lark(last_transliteration_line)
        lemma_line = []
        word_cnt = 0
        for token in ebl_lines.lines[0].content:
            unique_lemma = oracc_word_ebl_lemmas.get(word_cnt, [])
            if unique_lemma:
                lemma_line.append(LemmatizationToken(token.value, tuple(unique_lemma)))
                word_cnt += 1
            else:
                lemma_line.append(LemmatizationToken(token.value, None))
        return lemma_line

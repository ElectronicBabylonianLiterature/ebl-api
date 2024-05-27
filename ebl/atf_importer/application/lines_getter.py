from collections import defaultdict
from typing import Any, Dict, List, Tuple
from ebl.atf_importer.application.lemma_lookup import LemmaLookup
from ebl.atf_importer.application.glossary_parser import (
    GlossaryParserData,
)
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData


class EblLinesGetter:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger,
        glossary_data: GlossaryParserData,
    ):
        self.logger = logger
        self.lemmalookup = LemmaLookup(database, config, logger, glossary_data)

    def convert_to_ebl_lines(
        self,
        converted_lines: List[Dict[str, Any]],
        filename: str,
    ) -> Dict[str, List]:
        result = defaultdict(list)
        for line in converted_lines:
            result = self._handle_line_type(line, result, filename)
        return dict(result)

    def _handle_line_type(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
    ) -> defaultdict:
        c_type = line["c_type"]
        if c_type == "control_line":
            result = self._handle_control_line(line, result)
        elif c_type == "text_line":
            result = self._handle_text_line(line, result)
        elif c_type == "lem_line":
            result = self._handle_lem_line(line, result, filename)
        return result

    def _handle_control_line(self, line: Dict[str, Any], result: defaultdict):
        result["control_lines"].append(line)
        return result

    def _handle_text_line(
        self, line: Dict[str, Any], result: defaultdict
    ) -> defaultdict:
        transliteration = line["c_line"]
        result["last_transliteration"].append(transliteration)
        return result

    def _handle_lem_line(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
    ) -> defaultdict:
        if last_transliteration := result["last_transliteration"]:
            unique_lemmas = self._process_lemmatization(
                [item[0] for item in line["c_array"]], filename
            )
            result["lemmatization"].append((last_transliteration, unique_lemmas))
        else:
            self.logger.warning(
                f"Lemmatization line without preceding text line in {filename}"
            )
        return result

    def _process_lemmatization(
        self,
        lemma_tuples: List[Tuple[str, str, str]],
        filename: str,
    ) -> List[Dict]:
        unique_lemmas = []
        for lemma, guideword, pos_tag in lemma_tuples:
            if db_entries := self._lookup_lemma(lemma, guideword, pos_tag):
                unique_lemmas.extend(db_entries)
            else:
                self.logger.warning(f"Lemma not found: {lemma} in {filename}")
        return unique_lemmas

    def _lookup_lemma(
        self,
        lemma: str,
        guideword: str,
        pos_tag: str,
    ):
        return self.lemmalookup.lookup_lemma(lemma, guideword, pos_tag)

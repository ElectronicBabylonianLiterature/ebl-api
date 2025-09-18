from collections import defaultdict
from typing import Any, Dict, List, Tuple
from ebl.atf_importer.application.lemma_line_handler import LemmaLineHandler
from ebl.atf_importer.application.glossary import Glossary
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger
from ebl.atf_importer.domain.line_context import LineContext


class EblLinesGetter:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger: Logger,
        glossary: Glossary,
    ):
        self.logger = logger
        self.lemma_line_handler = LemmaLineHandler(database, config, logger, glossary)

    def convert_to_ebl_lines(
        self,
        converted_lines: List[Dict[str, Any]],
        filename: str,
    ) -> Dict[str, List]:
        line_context = LineContext(
            last_transliteration=[],
            last_transliteration_line=None,
            last_alter_lem_line_at=[],
        )
        result = defaultdict(list)
        for line in converted_lines:
            result, line_context = self._handle_line_type(
                line, result, filename, line_context
            )
        return dict(result)

    def _handle_line_type(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        line_context: LineContext,
    ) -> Tuple[defaultdict, LineContext]:
        c_type = line["c_type"]
        # ToDo: Clean up
        # print("!!!", c_type)
        # print(line["serialized"])
        if "control_line" in c_type:
            result = self._handle_control_line(line, result)
        elif c_type == "text_line":
            line_context = self._handle_text_line(line, result, line_context)
        elif c_type == "lem_line" and line_context.last_transliteration_line:
            lemmatized_line = self.lemma_line_handler.apply_lemmatization(
                line, result, filename, line_context.last_transliteration_line
            )
            if lemmatized_line:
                result["transliteration"][-1] = lemmatized_line
        elif "ebl_atf_at_line" in c_type or "ebl_atf_dollar_line" in c_type:
            result["transliteration"].append(line["serialized"])
        else:
            # ToDo:
            # Continue from here.
            # Handle `translation_line` correctly.
            # There should be a destingtion between proper translation lines
            # and those incorrectly parsed as translation line.
            # Check for other line types, then clean up
            if c_type not in ["empty_line"]:
                #input()
                result["transliteration"].append(line["serialized"])
                # result["lemmatization"].append(line["c_line"])
        return result, line_context

    def _handle_control_line(
        self, line: Dict[str, Any], result: defaultdict
    ) -> defaultdict:
        result["control_lines"].append(line)
        return result

    def _handle_text_line(
        self, line: Dict[str, Any], result: defaultdict, line_context: LineContext
    ) -> LineContext:
        line_context.last_transliteration = [
            entry for entry in line["c_array"] if entry != "DIŠ"
        ]
        line_context.last_transliteration_line = line["serialized"]
        line_context.last_alter_lem_line_at = line["c_alter_lem_line_at"]
        result["transliteration"].append(line_context.last_transliteration_line)
        return line_context

    def _log_line(self, filename: str, line_context: LineContext) -> None:
        self.logger.debug(
            f"{filename}: transliteration {str(line_context.last_transliteration_line)}"
        )
        self.logger.debug(
            f"eBL transliteration{str(line_context.last_transliteration)} "
            f"{len(line_context.last_transliteration)}"
        )

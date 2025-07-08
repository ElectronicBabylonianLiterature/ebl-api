from collections import defaultdict
from typing import Any, Dict, List, Tuple
from ebl.atf_importer.application.lemma_lookup import LemmaLineHandler
from ebl.atf_importer.application.glossary_parser import GlossaryParserData
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger
from ebl.atf_importer.domain.line_context import LineContext


# ToDo: Continue from here.
# The logic should be reconsidered and functionality transformed to `legacy_atf_converter`


class EblLinesGetter:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger: Logger,
        glossary_data: GlossaryParserData,
    ):
        self.logger = logger
        self.lemma_line_handler = LemmaLineHandler(
            database, config, logger, glossary_data
        )

    def convert_to_ebl_lines(
        self,
        converted_lines: List[Dict[str, Any]],
        filename: str,
    ) -> Dict[str, List]:
        context = LineContext(
            last_transliteration=[],
            last_transliteration_line="",
            last_alter_lem_line_at=[],
        )
        result = defaultdict(list)
        result["all_unique_lemmas"] = []
        for line in converted_lines:
            result, context = self._handle_line_type(line, result, filename, context)
        self._log_result(result, context)
        # ToDo: Fix & clean up
        try:
            return dict(result)
        except TypeError:
            return result

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
            result = self.lemma_line_handler.handle_lem_line(
                line, result, filename, context
            )
        else:
            result["transliteration"].append(line["serialized"])
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
        context.last_transliteration_line = line["serialized"]
        context.last_alter_lem_line_at = line["c_alter_lem_line_at"]
        result["transliteration"].append(context.last_transliteration_line)
        return context

    def _log_line(self, filename: str, context: LineContext) -> None:
        self.logger.debug(
            f"{filename}: transliteration {str(context.last_transliteration_line)}"
        )
        self.logger.debug(
            f"eBL transliteration{str(context.last_transliteration)} "
            f"{len(context.last_transliteration)}"
        )

    def _log_result(self, result: defaultdict, context: LineContext) -> None:
        all_unique_lemmas = result["all_unique_lemmas"]
        self.logger.debug(
            f"All unique lemmata. Total: {len(all_unique_lemmas)}.\n{str(all_unique_lemmas)}"
        )

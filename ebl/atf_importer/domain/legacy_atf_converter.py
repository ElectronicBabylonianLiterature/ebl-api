import codecs
from lark import Lark, ParseError
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Type, Any
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor
from ebl.atf_importer.domain.legacy_atf_visitor import (
    LegacyAtfVisitor,
    translation_block_transformer,
    column_transformer,
)
from ebl.transliteration.domain.line_transformer import LineTransformer
from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor
from ebl.atf_importer.domain.atf_conversions import (
    GetLemmaValuesAndGuidewords,
    GetWords,
)
from ebl.atf_importer.application.logger import Logger, LoggerUtil
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.line import EmptyLine, ControlLine
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.atf_importer.application.lemmatization import LemmaLookup
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.transliteration_error import (
    ExtentLabelError,
)
from ebl.atf_importer.domain.legacy_atf_line_validator import LegacyAtfLineValidator
from ebl.atf_importer.application.glossary import Glossary


glossary = Glossary(entries=[])


def include_line(line_instance) -> bool:
    if isinstance(line_instance, EmptyLine) or isinstance(line_instance, ControlLine):
        return False
    return True


class LegacyAtfConverter:
    ebl_parser = Lark.open(
        "../../transliteration/domain/atf_parsers/lark_parser/ebl_atf.lark",
        maybe_placeholders=True,
        rel_to=__file__,
    )
    indexing_visitor = IndexingVisitor()
    legacy_visitor = LegacyAtfVisitor()
    translation_block_transformer = translation_block_transformer[0]
    column_transformer = column_transformer[0]
    line_transformer = LineTransformer()

    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger: Logger,
        glossary: Glossary = glossary,
    ):
        self.logger = logger
        self.preprocessor = AtfPreprocessor(self.logger)
        self.lemmatization = LemmaLookup(database, config, logger, glossary)
        self.validate_text_line = LegacyAtfLineValidator().validate_text_line

    def convert_lines_from_string(self, text: str) -> Tuple[List[Dict[str, Any]], Text]:
        return self.atf_to_text(text.split("\n"))

    def convert_lines_from_path(
        self, path: str, filename: str
    ) -> Tuple[List[Dict[str, Any]], Text]:
        self.logger.info(LoggerUtil.print_frame(f'Converting: "{filename}.atf"'))
        with codecs.open(path, "r", encoding="utf8") as f:
            lines = f.read().split("\n")
        return self.atf_to_text(lines)

    def atf_to_text(self, lines: List[str]) -> Tuple[List[Dict[str, Any]], Text]:
        processed_lines = self.convert_lines(lines)
        text = Text(
            tuple(
                line["serialized"]
                for line in processed_lines
                if include_line(line["serialized"])
            ),
            ATF_PARSER_VERSION,
        )
        return processed_lines, text

    def convert_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        self.translation_block_transformer.reset()
        self.column_transformer.reset()
        processed_lines = []
        lines_data = self._parse_lines(lines)
        for line_data in lines_data:
            c_line, c_array, c_type, c_alter_lem_line_at = self._convert_line(
                line_data["string"], line_data["tree"]
            )
            result = {
                "c_line": c_line,
                "c_array": c_array,
                "c_type": c_type,
                "c_alter_lem_line_at": c_alter_lem_line_at,
                "serialized": None
                if line_data["tree"].data == "lem_line"
                else self.line_transformer.transform(line_data["tree"]),
            }
            processed_lines.append(result)
        self.logger.info(LoggerUtil.print_frame("Parsing finished"))
        return processed_lines

    def _convert_line(
        self, atf: str, tree: Tree
    ) -> Tuple[Any, Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        if tree.data == "lem_line":
            return self._convert_lem_line(atf, tree)
        else:
            self._log_line(atf, tree)
            return self._get_line_tree_data(tree)

    def _get_line_tree_data(self, tree: Tree) -> Tuple[Tree, List[Any], str, List[Any]]:
        words = self.serialize_words(tree)
        return tree, words, tree.data, []

    def _convert_lem_line(
        self, atf: str, tree: Tree
    ) -> Tuple[Optional[str], Optional[List[Any]], str, Optional[List[Any]]]:
        lemmas_and_guidewords_array = self.serizalize_lemmas_and_guidewords(tree)
        self._log_lem_line(tree, lemmas_and_guidewords_array)
        return atf, lemmas_and_guidewords_array, tree.data, []

    def _parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        self.indexing_visitor.reset()
        lines_data = []
        for line in lines:
            lines_data = self._parse_line(line, lines_data)
        return lines_data

    def _parse_line(
        self, line: str, lines_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        line_tree = self._parse_and_validate_line(line)
        self.legacy_visitor.visit(line_tree)
        if line_tree.data == "empty_line":
            return lines_data
        self.indexing_visitor.visit(line_tree)
        cursor = (
            self.indexing_visitor.cursor_index
            if line_tree.data == "text_line"
            else None
        )
        if (
            "translation_line" in line_tree.data
            and line_tree.data != "translation_line"
        ):
            return self._handle_legacy_translation(line_tree, lines_data)
        else:
            lines_data.append({"string": line, "tree": line_tree, "cursor": cursor})
            return lines_data

    def _parse_and_validate_line(self, line: str) -> Tree:
        try:
            line_tree = self.ebl_parser.parse(self.preprocessor.preprocess_line(line))
            if (
                line_tree.children[0].data == "legacy_translation_line"
                and not self.translation_block_transformer.active
                and "legacy_translation_block_at_line"
                not in line_tree.children[0].children[0].data
            ):
                raise ParseError
            elif line_tree.children[0].data == "text_line":
                if error := self.validate_text_line(line_tree.children[0]):
                    return self._report_and_correct_errors(line, error)
            return line_tree
        except (*PARSE_ERRORS, TransliterationError, ExtentLabelError) as error:
            return self._report_and_correct_errors(line, error)

    def _report_and_correct_errors(self, line: str, error: Type[Exception]) -> Tree:
        warning = (
            f"Error: {str(error)}\nThe following text line cannot be parsed:\n{line}"
        )
        self.logger.warning(warning)
        try:
            print(
                f"{warning}\nPlease input the corrected line, then press enter:",
            )
            corrected_line = input()
            return self._parse_and_validate_line(corrected_line)
        except (OSError, EOFError):
            return self.ebl_parser.parse("")

    def _handle_legacy_translation(
        self, translation_line: Tree, lines_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if translation_line.data == "!translation_line":
            translation_line.data = "translation_line"
            lines_data = self._insert_translation_line(translation_line, lines_data)
        return lines_data

    def _insert_translation_line(
        self, translation_line: Tree, lines_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for index, tree_line in enumerate(lines_data):
            insert_at = self.translation_block_transformer.start
            if insert_at == tree_line["cursor"]:
                insert_at_index = (
                    index + 2
                    if index + 2 <= len(lines_data)
                    and lines_data[index + 1]["tree"].data == "lem_line"
                    else index + 1
                )
                if (
                    insert_at_index < len(lines_data)
                    and lines_data[insert_at_index]["tree"].data == "translation_line"
                ):
                    lines_data[insert_at_index] = {
                        "string": "",
                        "tree": translation_line,
                        "cursor": None,
                    }
                else:
                    lines_data.insert(
                        insert_at_index,
                        {"string": "", "tree": translation_line, "cursor": None},
                    )
                break
        return lines_data

    def serialize_words(self, tree: Tree) -> List[Any]:
        words_serializer = GetWords()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        return words_serializer.result

    def serizalize_lemmas_and_guidewords(self, tree: Tree) -> List[Any]:
        lemmas_and_guidewords_serializer = GetLemmaValuesAndGuidewords()
        lemmas_and_guidewords_serializer.visit(tree)
        return lemmas_and_guidewords_serializer.result

    def _log_line(self, atf: str, tree: Tree) -> None:
        self.logger.debug(f"Original line: '{atf}'")
        self.logger.info("Line successfully parsed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info("".join("-" for _ in range(0, 70)))

    def _log_lem_line(
        self, tree: Tree, lemmas_and_guidewords_array: Optional[List[Any]]
    ) -> None:
        self.logger.debug(
            f"Converted line as {tree.data} --> '{str(lemmas_and_guidewords_array)}'"
        )
        self.logger.info("".join("-" for _ in range(0, 70)))

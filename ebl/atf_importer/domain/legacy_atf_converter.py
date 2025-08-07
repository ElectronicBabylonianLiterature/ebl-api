import codecs
from lark import Lark
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Any
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
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.atf_importer.application.lemma_lookup import LemmaLookup
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData


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
    skip_next_lem_line = False  # ToDo: Check & implement, if needed

    def __init__(
        self, database, config: AtfImporterConfigData, logger: Logger, glossary
    ):
        self.logger = logger
        self.preprocessor = AtfPreprocessor(self.logger)
        self.lemma_lookup = LemmaLookup(database, config, logger, glossary)

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
        # ToDo: Continue from here.
        # Importing legacy atf should include validation.
        # lines = [(line["serialized"], None) for line in line]
        # check_errors(lines)
        text = Text(
            tuple(
                line["serialized"]
                for line in processed_lines
                if not isinstance(line["serialized"], EmptyLine)
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
                "serialized": None  # ToDo: implement handling here?
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
        # ToDo: Continue from here. Correctly handle lemmatization
        if self.skip_next_lem_line:
            # ToDo: Perhaps restore logic (flag if previous is None)
            self.logger.warning("Skipping lem line due to previous flag.")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", [])
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
        line_tree = self.ebl_parser.parse(self.preprocessor.preprocess_line(line))
        self.indexing_visitor.visit(line_tree)
        self.legacy_visitor.visit(line_tree)
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

    def _handle_legacy_translation(
        self, translation_line: Tree, lines_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if translation_line.data == "!translation_line":
            translation_line.data = "translation_line"
            insert_at = self.translation_block_transformer.start
            lines_data = self._insert_translation_line(
                translation_line, insert_at, lines_data
            )
        return lines_data

    def _insert_translation_line(
        self, translation_line: Tree, insert_at: str, lines_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for index, tree_line in enumerate(lines_data):
            if insert_at == tree_line["cursor"]:
                if (
                    index + 1 < len(lines_data)
                    and lines_data[index + 1]["tree"].data == "translation_line"
                ):
                    lines_data[index + 1] = {
                        "string": "",
                        "tree": translation_line,
                        "cursor": None,
                    }
                else:
                    lines_data.insert(
                        index + 1,
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
        self.logger.info(
            "----------------------------------------------------------------------"
        )

    def _log_lem_line(
        self, tree: Tree, lemmas_and_guidewords_array: Optional[List[Any]]
    ) -> None:
        self.logger.debug(
            "Converted line as "
            + tree.data
            + " --> '"
            + str(lemmas_and_guidewords_array)
            + "'"
        )
        self.logger.info(
            "----------------------------------------------------------------------"
        )

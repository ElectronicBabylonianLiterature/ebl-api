import codecs
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Any
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.domain.legacy_atf_visitor import (
    LegacyAtfVisitor,
    translation_block_transformer,
    column_transformer,
)
from ebl.transliteration.domain.line_transformer import LineTransformer
from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor


class AtfPreprocessor(AtfPreprocessorBase):
    indexing_visitor = IndexingVisitor()
    legacy_visitor = LegacyAtfVisitor()
    translation_block_transformer = translation_block_transformer[0]
    column_transformer = column_transformer[0]
    line_transformer = LineTransformer()

    def convert_lines_from_string(self, text: str) -> List[Dict[str, Any]]:
        return self._convert_lines(text.split("\n"))

    def convert_lines_from_path(self, path: str, filename: str) -> List[Dict[str, Any]]:
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))
        with codecs.open(path, "r", encoding="utf8") as f:
            lines = f.read().split("\n")
        return self._convert_lines(lines)

    def _convert_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
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
        self.logger.info(Util.print_frame("Preprocessing finished"))
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
        if self.skip_next_lem_line:
            # ToDo: restore logic (flag if previous is None)
            self.logger.warning("Skipping lem line due to previous flag.")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", None)
        lemmas_and_guidewords_array = self.serizalize_lemmas_and_guidewords(tree)
        self._log_lem_line(tree, lemmas_and_guidewords_array)
        return atf, lemmas_and_guidewords_array, tree.data, []

    def _parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        self.indexing_visitor.reset()
        line_trees = []
        for line in lines:
            line_tree = self.ebl_parser.parse(self.preprocess_text(line))
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
                line_trees = self._handle_legacy_translation(line_tree, line_trees)
            else:
                line_trees.append({"string": line, "tree": line_tree, "cursor": cursor})
        return line_trees

    def _handle_legacy_translation(
        self, translation_line: Tree, line_trees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if translation_line.data == "!translation_line":
            translation_line.data = "translation_line"
            insert_at = self.translation_block_transformer.start
            line_trees = self._insert_translation_line(
                translation_line, insert_at, line_trees
            )
        return line_trees

    def _insert_translation_line(
        self, translation_line: Tree, insert_at: str, line_trees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for index, tree_line in enumerate(line_trees):
            if insert_at == tree_line["cursor"]:
                if (
                    index + 1 < len(line_trees)
                    and line_trees[index + 1]["tree"].data == "translation_line"
                ):
                    line_trees[index + 1] = {
                        "string": "",
                        "tree": translation_line,
                        "cursor": None,
                    }
                else:
                    line_trees.insert(
                        index + 1,
                        {"string": "", "tree": translation_line, "cursor": None},
                    )
                break
        return line_trees

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

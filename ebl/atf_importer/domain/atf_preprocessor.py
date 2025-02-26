import traceback
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Any
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.domain.legacy_atf_visitor import (
    LegacyAtfVisitor,
    translation_block_transformer,
    column_transformer,
)

# from ebl.transliteration.domain.line_transformer import LineTransformer
from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor


class AtfPreprocessor(AtfPreprocessorBase):
    indexing_visitor = IndexingVisitor()
    legacy_visitor = LegacyAtfVisitor()
    translation_block_transformer = translation_block_transformer[0]
    column_transformer = column_transformer[0]
    # line_transformer = LineTransformer()

    def convert_lines_from_string(self, text: str) -> List[Dict[str, Any]]:
        return self._convert_lines(text.split("\n"))

    def convert_lines_from_path(self, path: str, filename: str) -> List[Dict[str, Any]]:
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))
        lines = self.read_lines_from_path(path)
        return self._convert_lines(lines)

    def _parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        line_trees = []
        for line in lines:
            # ToDo: Parsing should happen here and ONLY here
            # Continue from here. Translation injection seems to work.
            # Now it should be properly tested.
            # For that, modify the logic and output a proper result.
            # Also, add column logic to detect the end of the text
            # and reset the legacy column transformer.

            line_tree = self.ebl_parser.parse(line)
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
                line_trees.append({"line": line_tree, "cursor": cursor})
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
                    and line_trees[index + 1]["line"].data == "translation_line"
                ):
                    line_trees[index + 1] = {
                        "cursor": None,
                        "line": translation_line,
                    }
                else:
                    line_trees.insert(
                        index + 1, {"cursor": None, "line": translation_line}
                    )
                break
        return line_trees

    def _convert_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        self.column_transformer.reset()
        line_trees = self._parse_lines(lines)  # ToDo: Implement further logic
        processed_lines = [line["line"] for line in line_trees]
        # processed_lines = []
        """
        for line in lines:
            result = self.process_line(line)
            # c_line = self.line_transformer.transform(result[0])
            processed_lines.append(
                {
                    "c_line": result[0],
                    "c_array": result[1],
                    "c_type": result[2],
                    "c_alter_lem_line_at": result[3],
                }
            )
        """
        self.logger.info(Util.print_frame("Preprocessing finished"))
        return processed_lines

    def get_line_tree_data(self, tree: Tree) -> Tuple[Tree, List[Any], str, List[Any]]:
        words = self.serialize_words(tree)
        return (tree, words, tree.data, [])

    def process_line(
        self, original_atf_line: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        # ToDo: Restructure. This should be made more straightforward, lines shouldn't be parsed twice.
        self.logger.debug(f"Original line: '{original_atf_line}'")
        atf_line = self.preprocess_text(original_atf_line)
        try:
            if atf_line.startswith("#lem"):
                raise Exception("Special handling for #lem lines.")
            return self.check_original_line(original_atf_line)
        except Exception:
            atf_line = (
                self.do_oracc_replacements(atf_line)
                if self.style == 0
                else self.do_cdli_replacements(atf_line)
            )
            return self.parse_and_convert_line(atf_line)

    def check_original_line(
        self, atf: str
    ) -> Tuple[Optional[Tree], List[Any], str, List[Any]]:
        if self.style == 2 and atf[0] == "#" and atf[1] == " ":
            atf = atf.replace("#", "#note:")
            atf = atf.replace("# note:", "#note:")
        tree = self.ebl_parser.parse(atf)
        tree = self.transform_legacy_atf(tree)
        self.logger.info("Line successfully parsed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return self.get_line_tree_data(tree)

    def transform_legacy_atf(self, tree: Tree) -> Tree:
        self.legacy_visitor.visit(tree)
        if self.legacy_visitor.legacy_found:
            self.logger.info("Legacy line successfully parsed")
        return tree

    def parse_and_convert_line(
        self, atf: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        result = (None, None, None, None)
        try:
            tree = self.ebl_parser.parse(atf)
            #if tree.data in self.unused_lines:
            # result = self.get_empty_conversion(tree)
            # ToDo: Check original
            # return tree
            if tree.data == "lem_line": # elif ...
                result = self.convert_lem_line(atf, tree)
            else:
                result = self.get_line_tree_data(tree)
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Could not convert line: {atf}", "unparsable_lines")
        return result

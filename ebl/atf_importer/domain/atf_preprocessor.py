import traceback
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Any
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.domain.legacy_atf_visitor import LegacyAtfVisitor
# from ebl.transliteration.domain.line_transformer import LineTransformer


class AtfPreprocessor(AtfPreprocessorBase):
    legacy_visitor = LegacyAtfVisitor()

    def convert_lines_from_string(self, text: str) -> List[Dict[str, Any]]:
        return self._convert_lines(text.split("\n"))

    def convert_lines_from_path(self, path: str, filename: str) -> List[Dict[str, Any]]:
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))
        lines = self.read_lines_from_path(path)
        return self._convert_lines(lines)

    def _convert_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        processed_lines = []
        for line in lines:
            result = self.process_line(line)
            processed_lines.append(
                {
                    "c_line": result[0],
                    "c_array": result[1],
                    "c_type": result[2],
                    "c_alter_lem_line_at": result[3],
                }
            )
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
        # print('!!!! visitor.legacy_found', visitor.legacy_found)
        if self.legacy_visitor.legacy_found:
            self.logger.info("Legacy line successfully parsed")
        return tree

    def parse_and_convert_line(
        self, atf: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        result = (None, None, None, None)
        try:
            tree = self.ebl_parser.parse(atf)
            if tree.data in self.unused_lines:
                # result = self.get_empty_conversion(tree)
                # ToDo: Check original
                return tree
            elif tree.data == "lem_line":
                result = self.convert_lem_line(atf, tree)
            else:
                result = self.get_line_tree_data(tree)
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Could not convert line: {atf}", "unparsable_lines")
        return result

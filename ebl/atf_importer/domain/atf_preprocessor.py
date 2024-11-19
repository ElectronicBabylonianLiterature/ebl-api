import traceback
from lark.visitors import Tree
from typing import Tuple, Optional, List, Dict, Any
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.domain.legacy_atf_visitor import LegacyAtfVisitor
# from ebl.transliteration.domain.line_transformer import LineTransformer


class AtfPreprocessor(AtfPreprocessorBase):
    def convert_lines(self, file: str, filename: str) -> List[Dict[str, Any]]:
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))

        lines = self.read_lines(file)
        processed_lines = []
        for line in lines:
            result = self.process_line(line)
            if self.stop_preprocessing:
                break
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

    def process_line(
        self, original_atf_line: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        # ToDo: Restructure. This should be made more straightforward, lines shouldn't be parsed twice.
        self.logger.debug(f"Original line: '{original_atf_line}'")
        atf_line = self.preprocess_text(original_atf_line)
        try:
            if atf_line.startswith("#lem"):
                raise Exception("Special handling for #lem lines.")
            if atf_line.startswith("@translation") or atf_line.startswith("@("):
                # ToDo: Handle translations
                # @translation labeled en project
                # @(t.e. 1)
                return self.parse_and_convert_line("")
            return self.check_original_line(original_atf_line)
        except Exception:
            atf_line = (
                self.do_oracc_replacements(atf_line)
                if self.style == 0
                else self.do_cdli_replacements(atf_line)
            )
            return self.parse_and_convert_line(atf_line)

    def check_original_line(self, atf: str) -> Tuple[str, List[Any], str, List[Any]]:
        print("! check_original_line.")
        if self.style == 2 and atf[0] == "#" and atf[1] == " ":
            atf = atf.replace("#", "#note:")
            atf = atf.replace("# note:", "#note:")
        # input(f"! before parse:\n{atf}")
        tree = self.ebl_parser.parse(atf)
        # print(tree.pretty())
        # input(f"! after parse:\n{self.line_tree_to_string(tree)}")
        # input("! before transform")
        # input("! after transform")
        tree = self.transform_legacy_atf(tree)
        self.logger.info("Line successfully parsed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return self.get_line_tree_data(tree)

    def transform_legacy_atf(self, tree: Tree) -> Tree:
        visitor = LegacyAtfVisitor()
        visitor.visit(tree)
        # print('!!!! visitor.legacy_found', visitor.legacy_found)
        if visitor.legacy_found:
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
            elif tree.data == "text_line":
                result = self.get_line_tree_data(tree)
            else:
                result = self.unused_line(tree)
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Could not convert line: {atf}", "unparsable_lines")
        return result

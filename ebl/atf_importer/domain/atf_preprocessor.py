import re
import traceback
from typing import Tuple, Optional, List, Dict, Any
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.domain.atf_conversions import GetWords
from lark import Lark
from lark.visitors import Visitor, Transformer, Tree, v_args

class HalfBracketsTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.legacy_found = False
        self.opened = False

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_OPEN_HALF_BRACKET(self, bracket: str) -> str:
        print("! bbbbbb", bracket)
        input()
        self.legacy_found = True
        self.opened = True
        return ""

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_CLOSE_HALF_BRACKET(self, bracket: str) -> str:
        print("! bbbbbb", bracket)
        self.legacy_found = True
        self.opened = False
        return ""

    @v_args(inline=True)
    def ebl_atf_text_line__flags(self, flags: str):
        return flags + "#" if self.open else flags


class OraccJoinerTransformer(Transformer):
    # ToDo: Implement in grammar
    def __init__(self):
        super().__init__()
        self.legacy_found = False

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_JOINER(self, bracket: str) -> str:
        self.legacy_found = True
        self.opened = False
        return ""

class OraccDividerTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.legacy_found = False
    # ToDo: Implement in grammar
    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_DIVIDER(self, bracket: str) -> str:
        self.legacy_found = True
        return "DIŠ"

class AccentedIndexTransformer(Transformer):
    replacement_chars = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ú": "u",
        "à": "a",
        "è": "e",
        "ì": "i",
        "ù": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ú": "U",
        "À": "A",
        "È": "E",
        "Ì": "I",
        "Ù": "U",
    }
    patterns = ((re.compile("[áéíúÁÉÍÚ]"), "₂"), (re.compile("[àèìùÀÈÌÙ]"), "₃"))

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        self.sub_index = None

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_VALUE_CHARACTER_ACCENTED(self, char: str) -> str:
        return self._transform_accented_vowel(char)

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_LOGOGRAM_CHARACTER_ACCENTED(self, char: str) -> str:
        return self._transform_accented_vowel(char)

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, char: Optional[str]) -> Optional[str]:
        return self.sub_index if self.sub_index and not char else char

    def _transform_accented_vowel(self, char: str) -> str:
        self._set_sub_index(char)
        self.legacy_found = True
        return self.replacement_chars[char]

    def _set_sub_index(self, char: str) -> None:
        for pattern, suffix in self.patterns:
            if match := pattern.search(char):
                self.sub_index = suffix


class LegacyAtfVisitor(Visitor):
    # ToDo: Continue from here.
    # Move all atf preprocessing here
    # ?Try to convert to string and then parse?
    def __init__(self):
        super().__init__()
        self.legacy_found = False

    def ebl_atf_text_line__legacy_accented_sign(self, tree: Tree) -> None:
        transformer = AccentedIndexTransformer().transform(tree)
        self._set_legacy(transformer)

    def ebl_atf_text_line__legacy_damage(self, tree: Tree) -> None:
        transformer = HalfBracketsTransformer().transform(tree)
        self._set_legacy(transformer)

    def _set_legacy(self, transformer):
        if transformer.legacy_found:
            self.legacy_found = True


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
                    "c_alter_lemline_at": result[3],
                }
            )
        self.logger.info(Util.print_frame("Preprocessing finished"))
        return processed_lines

    def process_line(
        self, original_atf_line: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
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
        self.ebl_parser.parse(atf)

        if self.style == 2 and atf[0] == "#" and atf[1] == " ":
            atf = atf.replace("#", "#note:")
            atf = atf.replace("# note:", "#note:")
        tree = self.oracc_parser.parse(atf)  # ToDo: Remove `oracc_parser`
        tree = self.transform_legacy_atf(tree)
        words_serializer = GetWords()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result

        self.logger.info("Line successfully parsed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return (atf, converted_line_array, tree.data, [])

    def transform_legacy_atf(self, tree: Tree) -> Tree:
        visitor = LegacyAtfVisitor()
        tree = visitor.visit(tree)
        if visitor.legacy_found:
            self.logger.info("Legacy line successfully parsed")
        return tree

    def parse_and_convert_line(
        self, atf: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        result = (None, None, None, None)
        try:
            tree = self.oracc_parser.parse(atf)
            if tree.data in self.unused_lines:
                result = self.get_empty_conversion(tree)
            elif tree.data == "lem_line":
                result = self.convert_lemline(atf, tree)
            elif tree.data == "text_line":
                result = self.handle_text_line(tree)
            else:
                result = self.unused_line(tree)
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Could not convert line: {atf}", "unparsable_lines")
        return result

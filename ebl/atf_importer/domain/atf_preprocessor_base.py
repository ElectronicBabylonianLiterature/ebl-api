import codecs
import logging
import re
from typing import Tuple, Optional, List, Any
from lark import Lark, Tree
from ebl.atf_importer.domain.atf_conversions import (
    # ConvertLineDividers,
    # ConvertLineJoiner,
    StripSigns,
    GetLemmaValuesAndGuidewords,
    GetWords,
    LineSerializer,
)

opening_half_bracket = {"⌈", "⸢"}
closing_half_bracket = {"⌉", "⸣"}


# ToDo:
# Functionality should be mainly transferred
# to `transformers`.
# Extract oracc_atf_lem_line parser,
# use within ebl_atf parser or separately.

unused_lines = {
    "oracc_atf_at_line__object_with_status",
    "oracc_atf_at_line__surface_with_status",
    "oracc_atf_at_line__discourse",
    "oracc_atf_at_line__column",
    "oracc_atf_at_line__seal",
    "dollar_line",
    "note_line",
    "control_line",
    "empty_line",
    "translation_line",
}

special_chars = {
    "sz": "š",
    "c": "š",
    "s,": "ṣ",
    "ş": "ṣ",
    "t,": "ṭ",
    "ḫ": "h",
    "j": "g",
    "ŋ": "g",
    "g̃": "g",
    "C": "Š",
    "SZ": "Š",
    "S,": "Ṣ",
    "Ş": "Ṣ",
    "T,": "Ṭ",
    "Ḫ": "H",
    "J": "G",
    "Ŋ": "G",
    "G̃": "G",
    "'": "ʾ",
}

oracc_replacements = {
    "{f}": "{munus}",
    "1/2": "½",
    "1/3": "⅓",
    "1/4": "¼",
    "1/5": "⅕",
    "1/6": "⅙",
    "2/3": "⅔",
    "5/6": "⅚",
    "\t": " ",
    "$ rest broken": "$ rest of side broken",
    "$ ruling": "$ single ruling",
    "$ seal impression broken": "$ (seal impression broken)",
    "$ seal impression": "$ (seal impression)",
}


preprocess_text_replacements = {
    "\r": "",
    "--": "-",
    "{f}": "{munus}",
    "1/2": "½",
    "1/3": "⅓",
    "1/4": "¼",
    "1/5": "⅕",
    "1/6": "⅙",
    "2/3": "⅔",
    "5/6": "⅚",
    "\t": " ",
    "$ rest broken": "$ rest of side broken",
    "$ ruling": "$ single ruling",
    "]x": "] x",
    "x[": "x [",
    "]⸢x": "] ⸢x",
    "]⌈x": "] ⌈x",
    "x⸣[": "x⸣ [",
    "x⌉[": "x⌉ [",
}


class AtfPreprocessorBase:
    def __init__(self, logdir: str, style: int) -> None:
        self.ebl_parser = Lark.open(
            "../../transliteration/domain/atf_parsers/lark_parser/ebl_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )

        # ToDo: Continue from here. Build the parser so it
        # handles ATF with legacy (CDLI & Oracc) syntax.
        # Previously: "lark-oracc/oracc_atf.lark",
        # This should be eventually removed completely.

        self.logger = logging.getLogger("Atf-Preprocessor")
        self.logger.setLevel(logging.DEBUG)
        self.skip_next_lem_line = False
        self.unused_lines = unused_lines
        self.stop_preprocessing = False
        self.logdir = logdir
        self.style = style
        self.open_found = False

    def preprocess_text(self, atf: str) -> str:
        for old, new in preprocess_text_replacements.items():
            atf = atf.replace(old, new)
        atf = re.sub(r"([\[<])([*:])(.*)", r"\1 \2\3", atf)
        atf = re.sub(r"(:)([]>])(.*)", r"\1 \2\3", atf)
        atf = " ".join(atf.split()).strip(" ")
        return atf

    def _normalize_numbers(self, digits: str) -> str:
        numbers = {str(i): f"₍{i}₎" for i in range(10)}
        return "".join(numbers.get(digit, digit) for digit in digits)

    def replace_special_characters(self, string: str) -> str:
        for old, new in special_chars.items():
            string = string.replace(old, new)
        return string

    def do_oracc_replacements(self, atf: str) -> str:
        for old, new in oracc_replacements.items():
            atf = atf.replace(old, new)
        atf = self.reorder_bracket_punctuation(atf)
        return self.do_cdli_replacements(atf)

    def do_cdli_replacements(self, atf: str) -> str:
        return (
            self._handle_text_line(atf)
            if atf[0].isdigit()
            else self._handle_dollar_line(atf)
        )

    def reorder_bracket_punctuation(self, atf: str) -> str:
        return re.sub(r"\]([\?!]+)", lambda match: match.group(1) + "]", atf)

    def unused_line(
        self, tree
    ) -> Tuple[Optional[str], Optional[List[Any]], str, Optional[List[Any]]]:
        if tree.data in self.unused_lines:
            return (self.line_tree_to_string(tree), None, tree.data, None)
        self.logger.warning(
            f"Attempting to process a line not marked as unused: {tree.data}"
        )
        return (None, None, tree.data, None)

    def convert_lem_line(
        self, atf: str, tree: Tree
    ) -> Tuple[Optional[str], Optional[List[Any]], str, Optional[List[Any]]]:
        if self.skip_next_lem_line:
            self.logger.warning("Skipping lem line due to previous flag.")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", None)
        lemmas_and_guidewords_array = self.serizalize_lemmas_and_guidewords(tree)
        self.logger.debug(
            "Converted line as "
            + tree.data
            + " --> '"
            + str(lemmas_and_guidewords_array)
            + "'"
        )
        return atf, lemmas_and_guidewords_array, tree.data, []

    def line_tree_to_string(self, tree: Tree) -> str:
        # ToDo: Remove
        line_serializer = LineSerializer()
        line_serializer.visit_topdown(tree)
        return line_serializer.line.strip(" ")

    def serialize_words(self, tree: Tree) -> List[Any]:
        words_serializer = GetWords()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        return words_serializer.result

    def serizalize_lemmas_and_guidewords(self, tree: Tree) -> List[Any]:
        lemmas_and_guidewords_serializer = GetLemmaValuesAndGuidewords()
        lemmas_and_guidewords_serializer.visit(tree)
        return lemmas_and_guidewords_serializer.result

    def get_line_tree_data(self, tree: Tree) -> Tuple[str, List[Any], str, List[Any]]:
        # ConvertLineDividers().visit(tree)
        # ConvertLineJoiner().visit(tree)
        StripSigns().visit(tree)  # ToDo: Move
        converted_line = self.line_tree_to_string(tree)
        input(f"converted line: {converted_line}")
        words = self.serialize_words(tree)
        return (converted_line, words, tree.data, [])

    def read_lines(self, file: str) -> List[str]:
        with codecs.open(file, "r", encoding="utf8") as f:
            return f.read().split("\n")

    def _handle_text_line(self, atf: str) -> str:
        atf_text_line_methods = [
            "_replace_dashes",
            "replace_special_characters",
            "_normalize_patterns",
            "_replace_primed_digits",
            "_process_bracketed_parts",
            "_uppercase_underscore",
            "_lowercase_braces",
            "_replace_dollar_signs",
            "_replace_tabs_and_excessive_whitespaces",
            "reorder_bracket_punctuation",
        ]
        for method_name in atf_text_line_methods:
            atf = getattr(self, method_name)(atf)
            # ToDo: Remove
            if atf.startswith("9. ⸢4(BÁN)?⸣"):
                print("atf after method " + method_name)
                print(atf)
                input("press enter")
        return atf

    def _replace_dashes(self, atf: str) -> str:
        return re.sub(r"–|--", "-", atf)

    def _normalize_patterns(self, atf: str) -> str:
        def callback_normalize(pat):
            return pat.group(1) + pat.group(2) + self._normalize_numbers(pat.group(3))

        return re.sub(r"(.*?)([a-zA-Z])(\d+)", callback_normalize, atf)

    def _replace_primed_digits(self, atf: str) -> str:
        return re.sub(r"(\d)ʾ", r"\1′", atf)

    def _uppercase_underscore(self, atf: str) -> str:
        def callback_upper(pat):
            return pat.group(1).upper().replace("-", ".")

        return re.sub(r"_(.*?)_", callback_upper, atf)

    def _lowercase_braces(self, atf: str) -> str:
        def callback_lower(pat):
            return pat.group(1).lower()

        return re.sub(r"({.*?})", callback_lower, atf)

    def _replace_dollar_signs(self, atf: str) -> str:
        return re.sub(r"\(\$.*\$\)", r"($___$)", atf)

    def _replace_tabs_and_excessive_whitespaces(self, atf: str) -> str:
        return atf.replace("[\t ]*", " ")

    def _handle_dollar_line(self, atf: str) -> str:
        special_marks = {
            "$ rest broken": "$ rest of side broken",
            "$ ruling": "$ single ruling",
        }
        if atf in special_marks.keys():
            return special_marks[atf]
        if atf.startswith("$ "):
            dollar_comment = atf.split("$ ")[1]
            return f"$ ({dollar_comment})"
        return atf

    def _process_bracketed_parts(self, atf: str) -> str:
        self.open_found = False
        split = re.split(r"([⌈⌉⸢⸣])", atf)
        # ToDo: Remove:
        if len(split) > 1 and atf.startswith("9. ⸢4(BÁN)?⸣"):
            # ToDo: Continue from here.
            # Problem with `4(BÁN)#?`, which is not in lark grammer
            # The issue is probably with SIGN - ? - #
            print("! split", split)
            print(
                "! norm", "".join(self._process_bracketed_part(part) for part in split)
            )
            input("press enter")
        return (
            "".join(self._process_bracketed_part(part) for part in split)
            if len(split) > 1
            else atf
        )

    def _process_bracketed_part(self, part: str) -> str:
        if part in opening_half_bracket.union(closing_half_bracket):
            self.open_found = part in opening_half_bracket
            return ""
        if not self.open_found:
            return part
        return re.sub(r"([-.\s])", r"#\1", part) + "#"

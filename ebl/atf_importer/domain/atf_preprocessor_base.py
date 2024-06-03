import codecs
import logging
import re
import traceback
from typing import Tuple, Optional, List, Any

from lark import Lark

from ebl.atf_importer.domain.atf_conversions import (
    ConvertLineDividers,
    ConvertLineJoiner,
    ConvertLegacyGrammarSigns,
    StripSigns,
    GetLemmaValuesAndGuidewords,
    GetWords,
    LineSerializer,
)

preprocess_text_replacements = {
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
    "$ seal impression broken": "$ (seal impression broken)",
    "$ seal impression": "$ (seal impression)",
}

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
    "$ seal impression broken": "$ (seal impression broken)",
    "$ seal impression": "$ (seal impression)",
}


class AtfPreprocessorBase:
    def __init__(self, logdir: str, style: int) -> None:
        self.ebl_parser = Lark.open(
            "../../transliteration/domain/ebl_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )
        self.oracc_parser = Lark.open(
            "lark-oracc/oracc_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )

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
        atf = " ".join(atf.split())
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
        atf = re.sub(r"([\[<])([*:])(.*)", r"\1 \2\3", atf)
        atf = re.sub(r"(:)([]>])(.*)", r"\1 \2\3", atf)
        atf = " ".join(atf.split())
        atr = self.reorder_bracket_punctuation(atf)
        return atf

    def reorder_bracket_punctuation(self, atf: str) -> str:
        return re.sub(r'\]([\?!]+)', lambda match: match.group(1) + ']', atf)

    def check_original_line(self, atf: str) -> Tuple[str, List[Any], str, List[Any]]:
        self.ebl_parser.parse(atf)

        # ToDo: Move condition to CDLI transformations?
        if self.style == 2 and atf[0] == "#" and atf[1] == " ":
            atf = atf.replace("#", "#note:")
            atf = atf.replace("# note:", "#note:")
        tree = self.oracc_parser.parse(atf)
        words_serializer = GetWords()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result

        self.logger.info("Line successfully parsed, no conversion needed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return (atf, converted_line_array, tree.data, [])

    def unused_line(
        self, tree
    ) -> Tuple[Optional[str], Optional[List[Any]], str, Optional[List[Any]]]:
        if tree.data in self.unused_lines:
            return self.get_empty_conversion(tree)
        self.logger.warning(
            f"Attempting to process a line not marked as unused: {tree.data}"
        )
        return (None, None, tree.data, None)

    def get_empty_conversion(self, tree) -> Tuple[str, None, str, None]:
        line_serializer = LineSerializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")
        return (converted_line, None, tree.data, None)

    def convert_lemline(
        self, atf: str, tree
    ) -> Tuple[Optional[str], Optional[List[Any]], str, Optional[List[Any]]]:
        if self.skip_next_lem_line:
            self.logger.warning("Skipping lem line due to previous flag.")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", None)

        lemmas_and_guidewords_serializer = GetLemmaValuesAndGuidewords()
        lemmas_and_guidewords_serializer.visit(tree)
        lemmas_and_guidewords_array = lemmas_and_guidewords_serializer.result

        self.logger.debug(
            "Converted line as "
            + tree.data
            + " --> '"
            + str(lemmas_and_guidewords_array)
            + "'"
        )
        return atf, lemmas_and_guidewords_array, tree.data, []

    def handle_text_line(self, tree) -> Tuple[str, List[Any], str, List[Any]]:
        ConvertLineDividers().visit(tree)
        ConvertLineJoiner().visit(tree)
        ConvertLegacyGrammarSigns().visit(tree)
        StripSigns().visit(tree)

        line_serializer = LineSerializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")

        words_serializer = GetWords()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        return (converted_line, words_serializer.result, tree.data, [])

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

    def read_lines(self, file: str) -> List[str]:
        with codecs.open(file, "r", encoding="utf8") as f:
            return f.read().split("\n")

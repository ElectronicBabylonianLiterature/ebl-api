import codecs
import logging
import re
import traceback

from lark import Lark

from ebl.atf_importer.domain.atf_conversions import (
    Convert_Line_Dividers,
    Convert_Line_Joiner,
    Convert_Legacy_Grammar_Signs,
    Strip_Signs,
    Get_Lemma_Values_and_Guidewords,
    Get_Words,
    Line_Serializer,
)
from ebl.atf_importer.domain.atf_preprocessor_util import Util


class ATFPreprocessor:
    def __init__(self, logdir, style):
        self.EBL_PARSER = Lark.open(
            "../../transliteration/domain/ebl_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )
        self.ORACC_PARSER = Lark.open(
            "lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__
        )

        self.logger = logging.getLogger("Atf-Preprocessor")
        self.logger.setLevel(10)
        self.skip_next_lem_line = False
        self.unparseable_lines = []
        self.unused_lines = [
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
        ]
        self.stop_preprocessing = False
        self.logdir = logdir
        self.style = style

    def do_oracc_replacements(self, atf):
        atf = re.sub(
            r"([\[<])([*:])(.*)", r"\1 \2\3", atf
        )  # convert [* => [  <* => < *
        atf = re.sub(r"(:)([]>])(.*)", r"\1 \2\3", atf)  # convert *] => * ]  ?
        atf = atf.replace("--", "-")  # new rule 22.02.2021
        atf = atf.replace("{f}", "{munus}")
        atf = atf.replace("1/2", "½")
        atf = atf.replace("1/3", "⅓")
        atf = atf.replace("1/4", "¼")
        atf = atf.replace("1/5", "⅕")
        atf = atf.replace("1/6", "⅙")
        atf = atf.replace("2/3", "⅔")

        atf = atf.replace("\t", " ")  # convert tabs to spaces
        atf = " ".join(atf.split())  # remove multiple spaces

        atf = atf.replace("$ rest broken", "$ rest of side broken")
        atf = atf.replace("$ ruling", "$ single ruling")
        atf = atf.replace("$ seal impression broken", "$ (seal impression broken)")
        return atf.replace("$ seal impression", "$ (seal impression)")

    def normalize_numbers(self, digits):
        numbers = {
            "0": "₀",
            "1": "₁",
            "2": "₂",
            "3": "₃",
            "4": "₄",
            "5": "₅",
            "6": "₆",
            "7": "₇",
            "8": "₈",
            "9": "₉",
        }

        return "".join(numbers[digit] for digit in digits)

    def replace_special_characters(self, string):
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

        for char in special_chars:
            string = string.replace(char, special_chars[char])

        return string

    def do_cdli_replacements(self, atf):
        if atf[0].isdigit():
            atf = atf.replace("–", "-")
            atf = atf.replace("--", "-")  # new rule 22.02.2021
            atf = self.replace_special_characters(atf)

            callback_normalize = (
                lambda pat: pat.group(1)
                + pat.group(2)
                + self.normalize_numbers(pat.group(3))
            )  # convert subscripts
            atf = re.sub(r"(.*?)([a-zA-Z])(\d+)", callback_normalize, atf)

            atf = re.sub(r"(\d)ʾ", r"\1′", atf)
            atfsplit = re.split(r"([⌈⸢])(.*)?([⌉⸣])", atf)
            opening = ["⌈", "⸢"]
            closing = ["⌉", "⸣"]

            open_found = False
            new_atf = ""
            for part in atfsplit:
                if open_found:
                    atf_part = part.replace("-", "#.")  # convert "-" to "."
                    atf_part = atf_part.replace("–", "#.")  # convert "-" to "."
                    atf_part = atf_part.replace(" ", "# ")  # convert " " to "#"
                    if atf_part not in opening and atf_part not in closing:
                        atf_part += "#"
                        new_atf += atf_part
                elif part not in opening and part not in closing:
                    new_atf += part

                if part in opening:
                    open_found = True
                elif part in closing:
                    open_found = False

            atf = new_atf

            def callback_upper(pat):
                return pat.group(1).upper().replace("-", ".")

            atf = re.sub(r"_(.*?)_", callback_upper, atf)  # convert "_xx_" to "XX"

            def callback_lower(pat):
                return pat.group(1).lower()  # lower {..} again

            atf = re.sub(r"({.*?})", callback_lower, atf)

            atf = re.sub(r"\(\$.*\$\)", r"($___$)", atf)

            atf = atf.replace("\t", " ")  # convert tabs to spaces
            atf = " ".join(atf.split())  # remove multiple spaces

        elif atf == "$ rest broken":
            atf = "$ rest of side broken"

        elif atf == "$ ruling":
            atf = "$ single ruling"

        elif atf == "$ seal impression broken":
            atf = "$ (seal impression broken)"

        elif atf == "$ seal impression":
            atf = "$ (seal impression)"

        return atf

    def do_c_atf_replacements(self, atf):
        if atf[0].isdigit():
            atf = atf.replace("–", "-")
            atf = atf.replace("--", "-")  # new rule 22.02.2021

            callback_normalize = (
                lambda pat: pat.group(1)
                + pat.group(2)
                + self.normalize_numbers(pat.group(3))
            )  # convert subscripts
            atf = re.sub(r"(.*?)([a-zA-Z])(\d+)", callback_normalize, atf)

            atf = self.replace_special_characters(atf)

            atfsplit = re.split(r"([⌈⸢])(.*)?([⌉⸣])", atf)
            opening = ["⌈", "⸢"]
            closing = ["⌉", "⸣"]

            open_found = False
            new_atf = ""
            for part in atfsplit:
                if open_found:
                    atf_part = part.replace("-", "#.")  # convert "-" to "."
                    atf_part = atf_part.replace("–", "#.")  # convert "-" to "."
                    atf_part = atf_part.replace(" ", "# ")  # convert " " to "#"
                    if atf_part not in opening and atf_part not in closing:
                        atf_part += "#"
                        new_atf += atf_part
                elif part not in opening and part not in closing:
                    new_atf += part

                if part in opening:
                    open_found = True
                elif part in closing:
                    open_found = False

            atf = new_atf

            def callback_upper(pat):
                return pat.group(1).upper().replace("-", ".")

            atf = re.sub(r"\(\$.*\$\)", r"($___$)", atf)

            atf = atf.replace("\t", " ")  # convert tabs to spaces
            atf = " ".join(atf.split())  # remove multiple spaces

        elif atf == "$ rest broken":
            atf = "$ rest of side broken"

        return atf

    def line_not_converted(self, original_atf, atf):
        error = "Could not convert line"
        self.logger.error(f"{error}: {atf}")
        self.logger.error(traceback.format_exc())

        if "translation" in atf:
            self.stop_preprocessing = True

        self.unparseable_lines.append(original_atf)
        return (None, None, None, None)

    def check_original_line(self, atf):
        self.EBL_PARSER.parse(atf)

        # special case convert note lines in cdli atf
        if self.style == 2 and atf[0] == "#" and atf[1] == " ":
            atf = atf.replace("#", "#note:")
            atf = atf.replace("# note:", "#note:")

        # words serializer oracc parser
        tree = self.ORACC_PARSER.parse(atf)
        # self.logger.debug((tree.pretty()))

        words_serializer = Get_Words()
        words_serializer.result = []
        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result

        self.logger.info("Line successfully parsed, no conversion needed")
        self.logger.debug(f"Parsed line as {tree.data}")
        self.logger.info(
            "----------------------------------------------------------------------"
        )
        return (atf, converted_line_array, tree.data, [])

    def unused_line(self, tree):
        for line in self.unused_lines:
            if tree.data == line:
                return self.get_empty_conversion(tree)

    def get_empty_conversion(self, tree):
        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")
        return (converted_line, None, tree.data, None)

    def convert_line(self, original_atf, atf):
        tree = self.ORACC_PARSER.parse(atf)
        self.logger.debug(f"Converting {tree.data}")

        # self.logger.debug((tree.pretty()))

        if tree.data == "lem_line":
            return self.convert_lemline(atf, tree)

        elif tree.data == "text_line":
            conversion_result = self.convert_textline(tree)
            return self.check_converted_line(original_atf, tree, conversion_result)

        else:
            return self.unused_line(tree)

    def convert_textline(self, tree):
        Convert_Line_Dividers().visit(tree)
        Convert_Line_Joiner().visit(tree)

        Convert_Legacy_Grammar_Signs().visit(tree)

        Strip_Signs().visit(tree)

        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")

        words_serializer = Get_Words()
        words_serializer.result = []
        words_serializer.alter_lemline_at = []

        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result
        return (converted_line, converted_line_array, words_serializer.alter_lemline_at)

    def check_converted_line(self, original_atf, tree, conversion):
        try:
            self.EBL_PARSER.parse(conversion[0])
            self.logger.debug("Successfully parsed converted line")
            self.logger.debug(conversion[0])
            self.logger.debug(f"Converted line as {tree.data} --> '{conversion[0]}'")
            self.logger.debug(
                "----------------------------------------------------------------------"
            )

            return (conversion[0], conversion[1], tree.data, conversion[2])

        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.error("Could not parse converted line")
            self.unparseable_lines.append(original_atf)
            return (None, None, None, None)

    def convert_lemline(self, atf, tree):
        if self.skip_next_lem_line:
            self.logger.warning("Skipping lem line")
            self.skip_next_lem_line = False
            return (None, None, "lem_line", None)

        lemmas_and_guidewords_serializer = Get_Lemma_Values_and_Guidewords()
        lemmas_and_guidewords_serializer.result = []
        lemmas_and_guidewords_serializer.visit(tree)
        lemmas_and_guidewords_array = lemmas_and_guidewords_serializer.result
        self.logger.debug(
            "Converted line as "
            + tree.data
            + " --> '"
            + str(lemmas_and_guidewords_array)
            + "'"
        )
        self.logger.debug(
            "----------------------------------------------------------------------"
        )

        return atf, lemmas_and_guidewords_array, tree.data, []

    def process_line(self, atf):
        self.logger.debug(f"Original line: '{atf}'")
        atf = atf.replace("\r", "")
        atf = atf.replace("sz", "š")
        original_atf = atf

        try:
            if atf.startswith("#lem"):
                raise Exception

            # try to parse line with ebl-parser
            return self.check_original_line(atf)

        except Exception:
            if self.style == 1:
                atf = self.do_c_atf_replacements(atf)
            elif self.style == 2:
                atf = self.do_cdli_replacements(atf)
            else:
                atf = self.do_oracc_replacements(atf)

            try:
                return self.convert_line(original_atf, atf)

            except Exception:
                return self.line_not_converted(original_atf, atf)

    def write_unparsable_lines(self, filename):
        with open(
            f"{self.logdir}unparseable_lines_{filename}.txt", "w", encoding="utf8"
        ) as outputfile:
            for key in self.unparseable_lines:
                outputfile.write(key + "\n")

    def read_lines(self, file):
        with codecs.open(file, "r", encoding="utf8") as f:
            atf_ = f.read()

        return atf_.split("\n")

    def convert_lines(self, file, filename):
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))

        lines = self.read_lines(file)
        processed_lines = []
        for line in lines:
            (c_line, c_array, c_type, c_alter_lemline_at) = self.process_line(line)

            if self.stop_preprocessing:
                break

            if c_line is not None:
                processed_lines.append(
                    {
                        "c_line": c_line,
                        "c_array": c_array,
                        "c_type": c_type,
                        "c_alter_lemline_at": c_alter_lemline_at,
                    }
                )
            elif c_type is None:
                self.skip_next_lem_line = True

        self.logger.info(Util.print_frame("Preprocessing finished"))
        self.write_unparsable_lines(filename)

        return processed_lines

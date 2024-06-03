import re
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase


opening_half_bracket = {"⌈", "⸢"}
closing_half_bracket = {"⌉", "⸣"}


class CdliReplacements(AtfPreprocessorBase):
    def do_cdli_replacements(self, atf: str) -> str:
        return (
            self._handle_text_line(atf)
            if atf[0].isdigit()
            else self._handle_dollar_line(atf)
        ).strip(" ")

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
            method = getattr(self, method_name)
            atf = method(atf)
        return atf

    def _replace_dashes(self, atf: str) -> str:
        return re.sub(r"–|--", "-", atf)

    def _normalize_patterns(self, atf: str) -> str:
        callback_normalize = (
            lambda pat: pat.group(1)
            + pat.group(2)
            + self._normalize_numbers(pat.group(3))
        )
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
        return atf.replace("[\t\s]*", " ")

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
        if len(split) > 1 and atf.startswith('10. ['):
            # ToDo: Continue from here.
            print("! split", split)
            print("! norm", "".join(self._process_bracketed_part(part) for part in split))
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
        if self.open_found == False:
            return part
        return re.sub(r"([-.\s])", r"#\1", part) + "#"

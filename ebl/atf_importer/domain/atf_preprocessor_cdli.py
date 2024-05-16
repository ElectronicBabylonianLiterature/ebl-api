import re
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase


class CdliReplacements(AtfPreprocessorBase):
    def do_cdli_replacements(self, atf: str) -> str:
        return (
            self._handle_numeric_atf(atf)
            if atf[0].isdigit()
            else self._handle_special_cases(atf)
        )

    def _handle_numeric_atf(self, atf: str) -> str:
        numeric_atf_methods = [
            "_replace_dashes",
            "replace_special_characters",
            "_normalize_patterns",
            "_replace_primed_digits",
            "_process_bracketed_parts",
            "_uppercase_underscore",
            "_lowercase_braces",
            "_replace_dollar_signs",
            "_replace_tabs",
        ]
        for method_name in numeric_atf_methods:
            method = getattr(self, method_name)
            atf = method(atf)
        return atf

    def _replace_dashes(self, atf: str) -> str:
        return atf.replace("–", "-").replace("--", "-")

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

    def _replace_tabs(self, atf: str) -> str:
        atf = atf.replace("\t", " ")
        return " ".join(atf.split())

    def _handle_special_cases(self, atf: str) -> str:
        special_cases = {
            "$ rest broken": "$ rest of side broken",
            "$ ruling": "$ single ruling",
            "$ seal impression broken": "$ (seal impression broken)",
            "$ seal impression": "$ (seal impression)",
        }
        return special_cases.get(atf, atf)

    def _process_bracketed_parts(self, atf: str) -> str:
        atfsplit = re.split(r"([⌈⸢])(.*)?([⌉⸣])", atf)
        opening = {"⌈", "⸢"}
        closing = {"⌉", "⸣"}

        new_atf = "".join(
            self._process_bracketed_part(part, opening, closing) for part in atfsplit
        )
        return new_atf

    def _process_bracketed_part(self, part: str, opening: set, closing: set) -> str:
        if getattr(self, "open_found", False):
            self.open_found = False if part in closing else self.open_found
            return self._transform_bracketed_part(part, opening, closing)
        if part in opening:
            self.open_found = True
        return part if part not in closing else ""

    def _transform_bracketed_part(self, part: str, opening: set, closing: set) -> str:
        part = part.replace("-", "#.").replace("–", "#.").replace(" ", "# ")
        if part not in opening and part not in closing:
            part += "#"
        return part

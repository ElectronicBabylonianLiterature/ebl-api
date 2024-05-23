import re
from ebl.atf_importer.domain.atf_preprocessor_base import AtfPreprocessorBase


class AtfCReplacements(AtfPreprocessorBase):
    def do_atf_c_replacements(self, atf: str) -> str:
        if atf[0].isdigit():
            atf = self._replace_hyphens(atf)
            atf = self._apply_normalization(atf)
            atf = self.replace_special_characters(atf)
            atf = self._process_split_replacements(atf)
            atf = self._replace_within_parentheses(atf)
            atf = self._normalize_whitespace(atf)
        return atf

    def _replace_hyphens(self, atf: str) -> str:
        return atf.replace("–", "-").replace("--", "-")

    def _apply_normalization(self, atf: str) -> str:
        def callback_normalize(pat):
            return pat.group(1) + pat.group(2) + self._normalize_numbers(pat.group(3))

        # ToDo: Check this. Does `callback_normalize` work?
        return re.sub(r"(.*?)([a-zA-Z])(\d+)", callback_normalize, atf)

    def _process_split_replacements(self, atf: str) -> str:
        atfsplit = re.split(r"([⌈⸢])(.*)?([⌉⸣])", atf)
        opening, closing = ["⌈", "⸢"], ["⌉", "⸣"]

        def replace_parts(part: str, open_found: bool) -> str:
            if open_found:
                return self._replace_with_special_rules(part)
            return part if part not in opening + closing else ""

        return self._build_new_atf(atfsplit, opening, closing, replace_parts)

    def _replace_with_special_rules(self, part: str) -> str:
        part = part.replace("-", "#.").replace("–", "#.").replace(" ", "# ")
        return f"{part}#" if part not in ["⌈", "⸢", "⌉", "⸣"] else part

    def _build_new_atf(
        self, atfsplit: list, opening: list, closing: list, replace_parts_func
    ) -> str:
        new_atf, open_found = "", False

        for part in atfsplit:
            new_atf += replace_parts_func(part, open_found)
            if part in opening:
                open_found = True
            elif part in closing:
                open_found = False

        return new_atf

    def _replace_within_parentheses(self, atf: str) -> str:
        return re.sub(r"\(\$.*\$\)", r"($___$)", atf)

    def _normalize_whitespace(self, atf: str) -> str:
        return " ".join(atf.replace("\t", " ").split())

import re
from ebl.atf_importer.application.logger import Logger

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


preprocess_text_replacements = {
    "\r": "",
    "\t": " ",
    "--": "-",
    "{f}": "{munus}",
    "1/2": "½",
    "1/3": "⅓",
    "1/4": "¼",
    "1/5": "⅕",
    "1/6": "⅙",
    "2/3": "⅔",
    "5/6": "⅚",
    "]x": "] x",
    "x[": "x [",
    "]⸢x": "] ⸢x",
    "]⌈x": "] ⌈x",
    "x⸣[": "x⸣ [",
    "x⌉[": "x⌉ [",
}

subscripts = {
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


class AtfPreprocessor:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def preprocess_line(self, atf: str) -> str:
        atf = atf.strip(" \r")
        return self.preprocess_line_by_type(atf)

    def preprocess_line_by_type(self, atf: str) -> str:
        if atf and atf[0].isdigit():
            for old, new in preprocess_text_replacements.items():
                atf = atf.replace(old, new)
            atf = self._handle_text_line(atf)
        elif atf and atf[0] == "$":
            atf = self._handle_dollar_line(atf)
        elif atf and atf[0] == "#":
            atf = self._handle_note_line(atf)
        return atf

    def _handle_text_line(self, atf: str) -> str:
        atf_text_line_methods = [
            "_replace_special_characters",
            "_uppercase_underscore",
            "_lowercase_braces",
            "_replace_tabulation",
            "_replace_tabs_and_excessive_whitespaces",
            "_reorder_bracket_punctuation",
        ]
        for method_name in atf_text_line_methods:
            atf = getattr(self, method_name)(atf)
        return atf

    def _handle_dollar_line(self, atf: str) -> str:
        if atf.startswith("$ "):
            dollar_comment = atf.split("$ ")[1]
            return f"$ ({dollar_comment})"
        return atf

    def _handle_note_line(self, atf: str) -> str:
        if atf[0] == "#" and atf[1] == " " and "# note:" not in atf:
            atf = atf.replace("#", "#note:")
        elif "# note:" in atf:
            atf = atf.replace("# note:", "#note:")
        return atf

    def _replace_special_characters(self, string: str) -> str:
        for old, new in special_chars.items():
            string = string.replace(old, new)
        return string

    def _reorder_bracket_punctuation(self, atf: str) -> str:
        return re.sub(
            r"([\]\u2e23\u2309])([?!]+)",
            lambda match: match.group(2) + match.group(1),
            atf,
        )

    def _uppercase_underscore(self, atf: str) -> str:
        def callback_upper(pat):
            return pat.group(1).upper().replace("-", ".")

        return re.sub(r"_(.*?)_", callback_upper, atf)

    def _lowercase_braces(self, atf: str) -> str:
        def callback_lower(m):
            content = m.group(1)

            def repl(part):
                if part.startswith("(") and part.endswith(")"):
                    return part
                else:
                    return part.lower()

            parts = re.split(r"(\(.*?\))", content)
            lowered = "".join((repl(part) for part in parts))
            return lowered

        return re.sub(r"{(.*?)}", lambda m: "{" + callback_lower(m) + "}", atf)

    def _replace_tabulation(self, atf: str) -> str:
        return re.sub(r"\(\$[^)]*\)", r"($___$)", atf)

    def _replace_tabs_and_excessive_whitespaces(self, atf: str) -> str:
        return re.sub(r"[\t ]+", " ", atf)

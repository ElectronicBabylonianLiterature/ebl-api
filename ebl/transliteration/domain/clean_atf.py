import re
from typing import List, Mapping

import attr
import pydash

from ebl.transliteration.domain.atf import (
    ATF_EXTENSIONS,
    Atf,
    CommentaryProtocol,
    FLAGS,
    VARIANT_SEPARATOR,
    WORD_SEPARATOR,
    UNKNOWN_NUMBER_OF_SIGNS,
    BROKEN_AWAY,
)
from ebl.transliteration.domain.side import Side

CONTROL_LINE = r"^(@|\$|#|&)"
MULTIPLEX_COMMENT = r"=:"
IGNORE_LINE_PATTERN = r"|".join([CONTROL_LINE, MULTIPLEX_COMMENT])


LACUNA: Mapping[str, str] = {
    "begin": re.escape(BROKEN_AWAY[Side.LEFT]),
    "end": re.escape(BROKEN_AWAY[Side.RIGHT]),
    "undeterminable": re.escape(UNKNOWN_NUMBER_OF_SIGNS),
}

LINE_NUMBER = r"^[^ ]+\.\s+"
OMISSION = r"<\(?[^>]+\)?>"
REMOVAL = r"<<[^>]+>>"
TABULATION = r"\(\$_+\$\)"
SHIFT = r"%\w+\s+"
ALTERNATIVE_DAMAGE = r"[⸢⸣]"
STRIP_PATTERN = r"|".join(
    [
        ATF_EXTENSIONS["erasure_illegible"],
        ATF_EXTENSIONS["erasure_boundary"],
        *[protocol.value for protocol in CommentaryProtocol],
        *FLAGS.values(),
        *LACUNA.values(),
        LINE_NUMBER,
        REMOVAL,
        OMISSION,
        TABULATION,
        SHIFT,
        ALTERNATIVE_DAMAGE,
    ]
)


DETERMINATIVE_OR_GLOSS = {"begin": r"\s*{+\+?", "end": r"}+({+\+?)?\s*?"}
DIVIDER = r"(^|\s+)(\||&\d*)(?=$|\s+)"
JOINER = r"(-|(?<! ):(?!= ))"
IN_WORD_NEWLINE = r"(?<! );(?!= )"
WHITE_SPACE_PATTERN = r"|".join(
    [*DETERMINATIVE_OR_GLOSS.values(), JOINER, IN_WORD_NEWLINE, DIVIDER]
)


BRACES_PATTERN = r"(?<![^\s])" r"\(([^\(\)]*)\)" r"(?!=[^\s])"


def _clean_line(line: str) -> str:
    result: str = pydash.reg_exp_replace(line, STRIP_PATTERN, "")
    result = pydash.reg_exp_replace(result, WHITE_SPACE_PATTERN, " ")
    result = pydash.reg_exp_replace(result, BRACES_PATTERN, r"\1")
    pydash.reg_exp_replace(result, r"\s+", " ")
    return result.strip()


def _clean_values(line: str) -> str:
    result = " ".join(map(_clean_value, line.split(" "))).strip()
    return pydash.reg_exp_replace(result, r"\s+", " ")


def _clean_value(value: str) -> str:
    grapheme = re.fullmatch(r"\|[^|]+\|", value)
    reading_with_sign = re.fullmatch(r"[^(]+\(([^)]+)\)", value)
    if VARIANT_SEPARATOR in value:
        return _clean_variant(value)
    elif grapheme or reading_with_sign:
        return value
    else:
        return _clean_reading(value)


def _clean_variant(value: str) -> str:
    return VARIANT_SEPARATOR.join(
        [_clean_value(part) for part in value.split(VARIANT_SEPARATOR)]
    )


def _clean_reading(value: str) -> str:
    result: str = pydash.reg_exp_replace(value, r"[.+]", " ")
    result = pydash.reg_exp_replace(result, r"@[^\s]+", "")
    return result.lower()


@attr.s(frozen=True, auto_attribs=True)
class CleanAtf:
    atf: Atf

    @property
    def cleaned(self) -> List[List[str]]:
        rows = map(_clean_line, self.filtered)
        rows = map(_clean_values, rows)
        return [row.split(WORD_SEPARATOR) for row in rows]

    @property
    def filtered(self) -> List[str]:
        return [
            line
            for line in self.atf.split("\n")
            if line and not re.match(IGNORE_LINE_PATTERN, line)
        ]

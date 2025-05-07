import re
import unicodedata
from enum import Enum, unique
from typing import Mapping, NewType, Optional

from ebl.transliteration.domain.side import Side

Atf = NewType("Atf", str)


ATF_PARSER_VERSION = "6.2.0"
DEFAULT_ATF_PARSER_VERSION = "0.1.0"


@unique
class Surface(Enum):
    """
    See "Surface" in
    http://oracc.org/doc/help/editinginatf/labels/index.html#d2e21408
    and "Surfaces" in
    http://oracc.org/doc/help/editinginatf/primer/structuretutorial/index.html#d2e17947
    """

    OBVERSE = ("obverse", "o")
    REVERSE = ("reverse", "r")
    BOTTOM = ("bottom", "b.e.")
    EDGE = ("edge", "e.")
    LEFT = ("left", "l.e.")
    RIGHT = ("right", "r.e.")
    TOP = ("top", "t.e.")
    SURFACE = ("surface", None)
    FACE = ("face", None)

    def __init__(self, atf: str, label: Optional[str]) -> None:
        self.atf = atf
        self.label = label

    @staticmethod
    def from_label(label: str) -> "Surface":
        return [enum for enum in Surface if enum.label == label][0]

    @staticmethod
    def from_atf(atf: str) -> "Surface":
        return [enum for enum in Surface if enum.atf == atf][0]


@unique
class Status(Enum):
    """See "Status" in
    http://oracc.org/doc/help/editinginatf/primer/structuretutorial/index.html
    """

    PRIME = "'"
    UNCERTAIN = "?"
    CORRECTION = "!"
    COLLATION = "*"


class DollarStatus(Enum):
    """
    Aliases CORRECTION and COLLATION are needed to load old format data from the DB.
    """

    COLLATED = "*"
    UNCERTAIN = "?"
    EMENDED_NOT_COLLATED = "!"
    NEEDS_COLLATION = "!?"
    NO_LONGER_VISIBLE = "°"

    CORRECTION = "!"
    COLLATION = "*"


@unique
class CommentaryProtocol(Enum):
    """See
    http://oracc.org/doc/help/editinginatf/commentary/index.html
    """

    QUOTATION = "!qt"
    BASE_TEXT = "!bs"
    COMMENTARY = "!cm"
    UNCERTAIN = "!zz"


@unique
class Flag(Enum):
    """See "Metadata" in
    http://oracc.org/doc/help/editinginatf/primer/inlinetutorial/index.html
    """

    DAMAGE = "#"
    UNCERTAIN = "?"
    CORRECTION = "!"
    COLLATION = "*"
    NO_LONGER_VISIBLE = "°"


@unique
class Joiner(Enum):
    HYPHEN = "-"
    DOT = "."
    PLUS = "+"
    COLON = ":"
    SEMICOLON = ";"
    COMMA = ","


@unique
class Ruling(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"


@unique
class Object(Enum):
    TABLET = "tablet"
    ENVELOPE = "envelope"
    PRISM = "prism"
    BULLA = "bulla"
    FRAGMENT = "fragment"
    OBJECT = "object"


@unique
class Scope(Enum):
    COLUMN = "column"
    COLUMNS = "columns"
    LINE = "line"
    LINES = "lines"
    CASE = "case"
    CASES = "cases"
    SIDE = "side"
    EXCERPT = "excerpt"
    SURFACE = "surface"


@unique
class Qualification(Enum):
    AT_LEAST = "at least"
    AT_MOST = "at most"
    ABOUT = "about"


@unique
class Extent(Enum):
    SEVERAL = "several"
    SOME = "some"
    REST_OF = "rest of"
    START_OF = "start of"
    BEGINNING_OF = "beginning of"
    MIDDLE_OF = "middle of"
    END_OF = "end of"


@unique
class State(Enum):
    BLANK = "blank"
    BROKEN = "broken"
    ILLEGIBLE = "illegible"
    MISSING = "missing"
    TRACES = "traces"
    OMITTED = "omitted"
    CONTINUES = "continues"
    EFFACED = "effaced"


@unique
class Discourse(Enum):
    CATCHLINE = "catchline"
    COLOPHON = "colophon"
    DATE = "date"
    SIGNATURE = "signature"
    SIGNATURES = "signatures"
    SUMMARY = "summary"
    WITNESSES = "witnesses"


@unique
class Composite(Enum):
    MILESTONE = "m=locator"
    COMPOSITE = "composite"
    DIV = "div"
    END = "end"


UNKNOWN_NUMBER_OF_SIGNS = "..."
WORD_SEPARATOR = " "
VARIANT_SEPARATOR = "/"
UNCLEAR_SIGN = "x"
UNIDENTIFIED_SIGN = "X"
IN_WORD_NEWLINE = ";"
TABULATION = "($___$)"
WORD_OMITTED = "ø"
LINE_BREAK = "|"
EGYPTIAN_METRICAL_FEET_SEPARATOR = "•"

ERASURE_BOUNDARY = "°"
ERASURE: Mapping[Side, str] = {
    Side.LEFT: ERASURE_BOUNDARY,
    Side.CENTER: "\\",
    Side.RIGHT: ERASURE_BOUNDARY,
}

BROKEN_AWAY: Mapping[Side, str] = {Side.LEFT: "[", Side.RIGHT: "]"}
PERHAPS_BROKEN_AWAY: Mapping[Side, str] = {Side.LEFT: "(", Side.RIGHT: ")"}
ACCIDENTAL_OMISSION: Mapping[Side, str] = {Side.LEFT: "<", Side.RIGHT: ">"}
INTENTIONAL_OMISSION: Mapping[Side, str] = {Side.LEFT: "<(", Side.RIGHT: ")>"}
REMOVAL: Mapping[Side, str] = {Side.LEFT: "<<", Side.RIGHT: ">>"}
EMENDATION: Mapping[Side, str] = {Side.LEFT: "<", Side.RIGHT: ">"}
DOCUMENT_ORIENTED_GLOSS: Mapping[Side, str] = {Side.LEFT: "{(", Side.RIGHT: ")}"}

COMPOUND_GRAPHEME_DELIMITER = "|"

FLAGS: Mapping[str, str] = {
    "uncertainty": re.escape(Flag.UNCERTAIN.value),
    "collation": re.escape(Flag.COLLATION.value),
    "damage": re.escape(Flag.DAMAGE.value),
    "no longer visible": re.escape(Flag.NO_LONGER_VISIBLE.value),
    "correction": re.escape(Flag.CORRECTION.value),
}


_SUB_SCRIPT: Mapping[str, str] = {
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉",
    "0": "₀",
}


def to_sub_index(number: Optional[int]) -> str:
    return (
        "ₓ"
        if number is None
        else ""
        if number == 1
        else "".join(_SUB_SCRIPT[digit] for digit in str(number))
    )


def sub_index_to_int(string: Optional[str]) -> Optional[int]:
    return (
        (None if string == "ₓ" else int(unicodedata.normalize("NFKC", string)))
        if string
        else 1
    )

import unicodedata
from enum import Enum
from typing import Mapping, NewType, Optional

import pydash

from ebl.transliteration.domain.side import Side

Atf = NewType("Atf", str)


ATF_PARSER_VERSION = "0.31.0"
DEFAULT_ATF_PARSER_VERSION = "0.1.0"


class AtfError(Exception):
    pass


class AtfSyntaxError(AtfError):
    def __init__(self, line_number):
        self.line_number = line_number
        message = f"Line {self.line_number} is invalid."
        super().__init__(message)


class Surface(Enum):
    """
See "Surface" in
http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html#d2e21408
and "Surfaces" in
http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html#d2e17947
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

    def __init__(self, atf: str, label: Optional[str]):
        self.atf = atf
        self.label = label

    @staticmethod
    def from_label(label: str) -> "Surface":
        return [enum for enum in Surface if enum.label == label][0]

    @staticmethod
    def from_atf(atf: str) -> "Surface":
        return [enum for enum in Surface if enum.atf == atf][0]


class Status(Enum):
    """ See "Status" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html
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

    CORRECTION = "!"
    COLLATION = "*"


class CommentaryProtocol(Enum):
    """ See
    http://oracc.museum.upenn.edu/doc/help/editinginatf/commentary/index.html
    """

    QUOTATION = "!qt"
    BASE_TEXT = "!bs"
    COMMENTARY = "!cm"
    UNCERTAIN = "!zz"


class Flag(Enum):
    """ See "Metadata" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html
    """

    DAMAGE = "#"
    UNCERTAIN = "?"
    CORRECTION = "!"
    COLLATION = "*"


class Joiner(Enum):
    HYPHEN = "-"
    DOT = "."
    PLUS = "+"
    COLON = ":"


class Ruling(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"


class Object(Enum):
    TABLET = "tablet"
    ENVELOPE = "envelope"
    PRISM = "prism"
    BULLA = "bulla"
    FRAGMENT = "fragment"
    OBJECT = "object"


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


class Qualification(Enum):
    AT_LEAST = "at least"
    AT_MOST = "at most"
    ABOUT = "about"


class Extent(Enum):
    N = "n"
    SEVERAL = "several"
    SOME = "some"
    REST_OF = "rest of"
    START_OF = "start of"
    BEGINNING_OF = "beginning of"
    MIDDLE_OF = "middle of"
    END_OF = "end of"


class State(Enum):
    BLANK = "blank"
    BROKEN = "broken"
    ILLEGIBLE = "illegible"
    MISSING = "missing"
    TRACES = "traces"
    OMITTED = "omitted"
    CONTINUES = "continues"


UNKNOWN_NUMBER_OF_SIGNS = "..."
WORD_SEPARATOR = " "
VARIANT_SEPARATOR = "/"
UNCLEAR_SIGN = "x"
UNIDENTIFIED_SIGN = "X"
IN_WORD_NEWLINE = ";"

ERASURE_BOUNDARY = "°"
ERASURE: Mapping[Side, str] = {
    Side.LEFT: ERASURE_BOUNDARY,
    Side.CENTER: "\\",
    Side.RIGHT: ERASURE_BOUNDARY,
}

BROKEN_AWAY: Mapping[Side, str] = {
    Side.LEFT: "[",
    Side.RIGHT: "]",
}
PERHAPS_BROKEN_AWAY: Mapping[Side, str] = {
    Side.LEFT: "(",
    Side.RIGHT: ")",
}
ACCIDENTAL_OMISSION: Mapping[Side, str] = {
    Side.LEFT: "<",
    Side.RIGHT: ">",
}
INTENTIONAL_OMISSION: Mapping[Side, str] = {
    Side.LEFT: "<(",
    Side.RIGHT: ")>",
}
REMOVAL: Mapping[Side, str] = {
    Side.LEFT: "<<",
    Side.RIGHT: ">>",
}
DOCUMENT_ORIENTED_GLOSS: Mapping[Side, str] = {
    Side.LEFT: "{(",
    Side.RIGHT: ")}",
}

COMPOUND_GRAPHEME_DELIMITER = "|"

FLAGS: Mapping[str, str] = {
    "uncertainty": pydash.escape_reg_exp(Flag.UNCERTAIN.value),
    "collation": pydash.escape_reg_exp(Flag.COLLATION.value),
    "damage": pydash.escape_reg_exp(Flag.DAMAGE.value),
    "correction": pydash.escape_reg_exp(Flag.CORRECTION.value),
}

ATF_SPEC: Mapping[str, str] = {
    "reading": r"([^₀-₉ₓ/]+)([₀-₉]+)?",
    "with_sign": r"[^\(/\|]+\((.+)\)",
    "grapheme": r"\|([.x×%&+@]?(\d+[.x×%&+@])?\(?[A-ZṢŠṬ₀-₉ₓ]+([@~][a-z0-9]+)*\)?)+\|",
    "number": r"\d+",
    "variant": r"([^/]+)(?:/([^/]+))+",
}

ATF_EXTENSIONS: Mapping[str, str] = {
    "erasure_boundary": ERASURE_BOUNDARY,
    "erasure_delimiter": ERASURE[Side.CENTER],
    "erasure_illegible": r"°[^\°]*\\",
    "line_continuation": "→",
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
        1
        if not string
        else None
        if string == "ₓ"
        else int(unicodedata.normalize("NFKC", string))
    )

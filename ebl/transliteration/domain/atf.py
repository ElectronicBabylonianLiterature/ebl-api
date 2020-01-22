import unicodedata
from enum import Enum
from typing import Mapping, NewType, Optional

import pydash
from pyoracc.atf.common.atffile import AtfFile

from ebl.transliteration.domain.side import Side

Atf = NewType("Atf", str)


ATF_PARSER_VERSION = "0.26.0"
DEFAULT_ATF_PARSER_VERSION = "0.1.0"


class AtfError(Exception):
    pass


class AtfSyntaxError(AtfError):
    def __init__(self, line_number):
        self.line_number = line_number
        message = f"Line {self.line_number} is invalid."
        super().__init__(message)


def validate_atf(text):
    prefix = "\n".join(ATF_HEADING)
    try:
        return AtfFile(f"{prefix}\n{text}", atftype="oracc")
    except SyntaxError as error:
        line_number = error.lineno - len(ATF_HEADING)
        raise AtfSyntaxError(line_number)
    except Exception as error:
        raise AtfError(f"Pyoracc validation failed: {error}.")


class Surface(Enum):
    """ See "Surface" in
    http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html
    """

    OBVERSE = ("@obverse", "o")
    REVERSE = ("@reverse", "r")
    BOTTOM = ("@bottom", "b.e.")
    EDGE = ("@edge", "e.")
    LEFT = ("@left", "l.e.")
    RIGHT = ("@right", "r.e.")
    TOP = ("@top", "t.e.")

    def __init__(self, atf, label):
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


class SurfaceScope(Enum):
    OBVERSE = "obverse"
    REVERSE = "reverse"
    BOTTOM = "bottom"
    EDGE = "edge"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"


class ObjectScope(Enum):
    TABLET = "tablet"
    ENVELOPE = "envelope"
    PRISM = "prism"
    BULLA = "bulla"
    FRAGMENT = "fragment"
    OBJECT = "object"


class ScopeScope(Enum):
    COLUMN = "column"
    COLUMNS = "columns"
    LINE = "line"
    LINES = "lines"
    CASE = "case"
    CASES = "cases"
    SIDE = "side"
    EXCERPT = "excerpt"


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

COMPOUND_GRAPHEME_DELIMITER = "|"

FLAGS: Mapping[str, str] = {
    "uncertainty": pydash.escape_reg_exp(Flag.UNCERTAIN.value),
    "collation": pydash.escape_reg_exp(Flag.COLLATION.value),
    "damage": pydash.escape_reg_exp(Flag.DAMAGE.value),
    "correction": pydash.escape_reg_exp(Flag.CORRECTION.value),
}

LACUNA: Mapping[str, str] = {
    "begin": r"\[",
    "end": r"\]",
    "undeterminable": pydash.escape_reg_exp(UNKNOWN_NUMBER_OF_SIGNS),
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


ATF_HEADING = [
    "&XXX = XXX",
    "#project: eblo",
    "#atf: lang akk-x-stdbab",
    "#atf: use unicode",
    "#atf: use math",
    "#atf: use legacy",
]


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


def int_to_sub_index(number: int) -> str:
    return "" if number == 1 else "".join(_SUB_SCRIPT[digit] for digit in str(number))


def sub_index_to_int(string: Optional[str]) -> int:
    return int(unicodedata.normalize("NFKC", string)) if string else 1

from typing import List

from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import (
    Joiner,
    Token,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import InWordNewline


def broken_away_gap() -> List[Token]:
    return [BrokenAway.open(), UnknownNumberOfSigns.of(), BrokenAway.close()]


def broken_away_gap_start() -> List[Token]:
    return [BrokenAway.open(), UnknownNumberOfSigns.of()]


def broken_away_gap_end() -> List[Token]:
    return [UnknownNumberOfSigns.of(), BrokenAway.close()]


def damaged_unclear_sign() -> List[Token]:
    return [UnclearSign.of([Flag.DAMAGE])]


def ki_du() -> List[Token]:
    return [
        Reading.of((ValueToken.of("k"), BrokenAway.close(), ValueToken.of("i"))),
        Joiner.hyphen(),
        Reading.of_name("du"),
    ]


def u() -> List[Token]:
    return [Reading.of_name("u")]


def ba_ma_ti() -> List[Token]:
    return [
        Reading.of_name("ba"),
        Joiner.hyphen(),
        Reading.of_name("ma"),
        Joiner.hyphen(),
        Reading.of((ValueToken.of("t"), BrokenAway.open(), ValueToken.of("i"))),
    ]


def mu() -> List[Token]:
    return [Reading.of_name("mu")]


def ta_ma_tu() -> List[Token]:
    return [
        Reading.of_name("ta"),
        Joiner.hyphen(),
        Reading.of_name("ma"),
        InWordNewline.of(),
        Joiner.hyphen(),
        Reading.of_name("tu", 2),
    ]

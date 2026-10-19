"""Parsed-word test cases, part 4 of 5."""

from typing import List, Sequence

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Determinative,
    Erasure,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.sign_tokens import (
    Logogram,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    Token,
    UnknownNumberOfSigns,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    Word,
)


def erased_e_over_li() -> List[Token]:
    return [
        Erasure.open(),
        Reading.of_name("e").set_erasure(ErasureState.ERASED),
        Erasure.center(),
        Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
        Erasure.close(),
    ]


def hyphenated_word(*parts: Sequence[Token]) -> Word:
    tokens: List[Token] = []
    for index, part in enumerate(parts):
        if index:
            tokens.append(Joiner.hyphen())
        tokens.extend(part)
    return Word.of(tokens)


def reading(name: str) -> List[Token]:
    return [Reading.of_name(name)]


def unknown_signs() -> List[Token]:
    return [UnknownNumberOfSigns.of()]


WORD_CASES = [
    (
        "me-°e\\li°-ku",
        hyphenated_word(reading("me"), erased_e_over_li(), reading("ku")),
    ),
    (
        "me-°e\\li°-me-°e\\li°-ku",
        hyphenated_word(
            reading("me"),
            erased_e_over_li(),
            reading("me"),
            erased_e_over_li(),
            reading("ku"),
        ),
    ),
    (
        "...{d}kur",
        Word.of(
            [
                UnknownNumberOfSigns.of(),
                Determinative.of([Reading.of_name("d")]),
                Reading.of_name("kur"),
            ]
        ),
    ),
    (
        "kur{d}...",
        Word.of(
            [
                Reading.of_name("kur"),
                Determinative.of([Reading.of_name("d")]),
                UnknownNumberOfSigns.of(),
            ]
        ),
    ),
    (
        "...-kur-...",
        hyphenated_word(unknown_signs(), reading("kur"), unknown_signs()),
    ),
    (
        "kur-...-kur-...-kur",
        hyphenated_word(
            reading("kur"),
            unknown_signs(),
            reading("kur"),
            unknown_signs(),
            reading("kur"),
        ),
    ),
    (
        "...]-ku",
        hyphenated_word([UnknownNumberOfSigns.of(), BrokenAway.close()], reading("ku")),
    ),
    (
        "ku-[...",
        hyphenated_word(reading("ku"), [BrokenAway.open(), UnknownNumberOfSigns.of()]),
    ),
    (
        "....ku",
        Word.of([UnknownNumberOfSigns.of(), Joiner.dot(), Reading.of_name("ku")]),
    ),
    (
        "ku....",
        Word.of([Reading.of_name("ku"), Joiner.dot(), UnknownNumberOfSigns.of()]),
    ),
    (
        "(x)]",
        Word.of(
            [
                PerhapsBrokenAway.open(),
                UnclearSign.of(),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
            ]
        ),
    ),
    (
        "[{d}UTU",
        Word.of(
            [
                BrokenAway.open(),
                Determinative.of([Reading.of_name("d")]),
                Logogram.of_name("UTU"),
            ]
        ),
    ),
    (
        "{m#}[{d}AG-sa-lim",
        hyphenated_word(
            [
                Determinative.of([Reading.of_name("m", flags=[atf.Flag.DAMAGE])]),
                BrokenAway.open(),
                Determinative.of([Reading.of_name("d")]),
                Logogram.of_name("AG"),
            ],
            reading("sa"),
            reading("lim"),
        ),
    ),
]

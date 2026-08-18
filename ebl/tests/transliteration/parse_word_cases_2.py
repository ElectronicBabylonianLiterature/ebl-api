"""Parsed-word test cases, part 2 of 5."""

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.sign_tokens import (
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import Word

WORD_CASES = [
    (
        "i-le-ʾe-[e",
        Word.of(
            [
                Reading.of_name("i"),
                Joiner.hyphen(),
                Reading.of_name("le"),
                Joiner.hyphen(),
                Reading.of_name("ʾe"),
                Joiner.hyphen(),
                BrokenAway.open(),
                Reading.of_name("e"),
            ]
        ),
    ),
    (
        "U₄.27/29.KAM",
        Word.of(
            [
                Logogram.of_name("U", 4),
                Joiner.dot(),
                Variant.of(Number.of_name("27"), Number.of_name("29")),
                Joiner.dot(),
                Logogram.of_name("KAM"),
            ]
        ),
    ),
    (
        "x/m[a",
        Word.of(
            [
                Variant.of(
                    UnclearSign.of(),
                    Reading.of(
                        (ValueToken.of("m"), BrokenAway.open(), ValueToken.of("a"))
                    ),
                )
            ]
        ),
    ),
    (
        "SAL.{+mu-ru-ub}",
        Word.of(
            [
                Logogram.of_name("SAL"),
                Joiner.dot(),
                PhoneticGloss.of(
                    [
                        Reading.of_name("mu"),
                        Joiner.hyphen(),
                        Reading.of_name("ru"),
                        Joiner.hyphen(),
                        Reading.of_name("ub"),
                    ]
                ),
            ]
        ),
    ),
    (
        "{+mu-ru-ub}[LA",
        Word.of(
            [
                PhoneticGloss.of(
                    [
                        Reading.of_name("mu"),
                        Joiner.hyphen(),
                        Reading.of_name("ru"),
                        Joiner.hyphen(),
                        Reading.of_name("ub"),
                    ]
                ),
                BrokenAway.open(),
                Logogram.of_name("LA"),
            ]
        ),
    ),
    (
        "I.{d}",
        Word.of(
            [
                Logogram.of_name("I"),
                Joiner.dot(),
                Determinative.of([Reading.of_name("d")]),
            ]
        ),
    ),
    (
        "{d}[UTU?",
        Word.of(
            [
                Determinative.of([Reading.of_name("d")]),
                BrokenAway.open(),
                Logogram.of_name("UTU", flags=[atf.Flag.UNCERTAIN]),
            ]
        ),
    ),
    (
        "3.AM₃",
        Word.of([Number.of_name("3"), Joiner.dot(), Logogram.of_name("AM", 3)]),
    ),
    (
        "<{10}>bu",
        Word.of(
            [
                AccidentalOmission.open(),
                Determinative.of([Number.of_name("10")]),
                AccidentalOmission.close(),
                Reading.of_name("bu"),
            ]
        ),
    ),
    (
        "KA₂?].DINGIR.RA[{ki?}",
        Word.of(
            [
                Logogram.of_name("KA", 2, flags=[atf.Flag.UNCERTAIN]),
                BrokenAway.close(),
                Joiner.dot(),
                Logogram.of_name("DINGIR"),
                Joiner.dot(),
                Logogram.of_name("RA"),
                BrokenAway.open(),
                Determinative.of([Reading.of_name("ki", flags=[atf.Flag.UNCERTAIN])]),
            ]
        ),
    ),
    (
        "{d?}nu?-di]m₂?-mu[d?",
        Word.of(
            [
                Determinative.of([Reading.of_name("d", flags=[atf.Flag.UNCERTAIN])]),
                Reading.of_name("nu", flags=[atf.Flag.UNCERTAIN]),
                Joiner.hyphen(),
                Reading.of(
                    (ValueToken.of("di"), BrokenAway.close(), ValueToken.of("m")),
                    2,
                    flags=[atf.Flag.UNCERTAIN],
                ),
                Joiner.hyphen(),
                Reading.of(
                    (ValueToken.of("mu"), BrokenAway.open(), ValueToken.of("d")),
                    flags=[atf.Flag.UNCERTAIN],
                ),
            ]
        ),
    ),
    (
        "<GAR?>",
        Word.of(
            [
                AccidentalOmission.open(),
                Logogram.of_name("GAR", flags=[atf.Flag.UNCERTAIN]),
                AccidentalOmission.close(),
            ]
        ),
    ),
    (
        "<<GAR>>",
        Word.of([Removal.open(), Logogram.of_name("GAR"), Removal.close()]),
    ),
    ("lu₂@v", Word.of([Reading.of_name("lu", 2, modifiers=["@v"])])),
]

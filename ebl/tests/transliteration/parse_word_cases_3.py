"""Parsed-word test cases, part 3 of 5."""

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    Erasure,
    IntentionalOmission,
)
from ebl.transliteration.domain.sign_tokens import (
    Logogram,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    Word,
)

WORD_CASES = [
    (
        "{lu₂@v}UM.ME.[A",
        Word.of(
            [
                Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])]),
                Logogram.of_name("UM"),
                Joiner.dot(),
                Logogram.of_name("ME"),
                Joiner.dot(),
                BrokenAway.open(),
                Logogram.of_name("A"),
            ]
        ),
    ),
    (
        "{lu₂@v}]KAB.SAR-M[EŠ",
        Word.of(
            [
                Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])]),
                BrokenAway.close(),
                Logogram.of_name("KAB"),
                Joiner.dot(),
                Logogram.of_name("SAR"),
                Joiner.hyphen(),
                Logogram.of(
                    (ValueToken.of("M"), BrokenAway.open(), ValueToken.of("EŠ"))
                ),
            ]
        ),
    ),
    (
        "MIN<(ta-ne₂-hi)>",
        Word.of(
            [
                Logogram.of_name("MIN").with_surrogate(
                    [
                        Reading.of_name("ta"),
                        Joiner.hyphen(),
                        Reading.of_name("ne", 2),
                        Joiner.hyphen(),
                        Reading.of_name("hi"),
                    ]
                )
            ]
        ),
    ),
    (
        "MIN<(mu-u₂)>",
        Word.of(
            [
                Logogram.of_name("MIN").with_surrogate(
                    [
                        Reading.of_name("mu"),
                        Joiner.hyphen(),
                        Reading.of_name("u", 2),
                    ]
                )
            ]
        ),
    ),
    (
        "KIMIN<(mu-u₂)>",
        Word.of(
            [
                Logogram.of_name("KIMIN").with_surrogate(
                    [
                        Reading.of_name("mu"),
                        Joiner.hyphen(),
                        Reading.of_name("u", 2),
                    ]
                )
            ]
        ),
    ),
    ("UN#", Word.of([Logogram.of_name("UN", flags=[atf.Flag.DAMAGE])])),
    (
        "he₂-<(pa₃)>",
        Word.of(
            [
                Reading.of_name("he", 2),
                Joiner.hyphen(),
                IntentionalOmission.open(),
                Reading.of_name("pa", 3),
                IntentionalOmission.close(),
            ]
        ),
    ),
    (
        "[{i]ti}AB",
        Word.of(
            [
                BrokenAway.open(),
                Determinative.of(
                    [
                        Reading.of(
                            (
                                ValueToken.of("i"),
                                BrokenAway.close(),
                                ValueToken.of("ti"),
                            )
                        )
                    ]
                ),
                Logogram.of_name("AB"),
            ]
        ),
    ),
    ("in]", Word.of([Reading.of_name("in"), BrokenAway.close()])),
    (
        "<en-da-ab>",
        Word.of(
            [
                AccidentalOmission.open(),
                Reading.of_name("en"),
                Joiner.hyphen(),
                Reading.of_name("da"),
                Joiner.hyphen(),
                Reading.of_name("ab"),
                AccidentalOmission.close(),
            ]
        ),
    ),
    (
        "me-e-li-°\\ku°",
        Word.of(
            [
                Reading.of_name("me"),
                Joiner.hyphen(),
                Reading.of_name("e"),
                Joiner.hyphen(),
                Reading.of_name("li"),
                Joiner.hyphen(),
                Erasure.open(),
                Erasure.center(),
                Reading.of_name("ku").set_erasure(ErasureState.OVER_ERASED),
                Erasure.close(),
            ]
        ),
    ),
    (
        "°me-e-li\\°-ku",
        Word.of(
            [
                Erasure.open(),
                Reading.of_name("me").set_erasure(ErasureState.ERASED),
                Joiner.hyphen().set_erasure(ErasureState.ERASED),
                Reading.of_name("e").set_erasure(ErasureState.ERASED),
                Joiner.hyphen().set_erasure(ErasureState.ERASED),
                Reading.of_name("li").set_erasure(ErasureState.ERASED),
                Erasure.center(),
                Erasure.close(),
                Joiner.hyphen(),
                Reading.of_name("ku"),
            ]
        ),
    ),
]

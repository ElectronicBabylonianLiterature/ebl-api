"""Lone-determinative parsed-word test cases."""

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
)
from ebl.transliteration.domain.sign_tokens import (
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative

LONE_DETERMINATIVE_CASES = [
    (
        "<{10}>",
        LoneDeterminative.of(
            [
                AccidentalOmission.open(),
                Determinative.of([Number.of_name("10")]),
                AccidentalOmission.close(),
            ]
        ),
    ),
    (
        "{ud]u?}",
        LoneDeterminative.of(
            [
                Determinative.of(
                    [
                        Reading.of(
                            (
                                ValueToken.of("ud"),
                                BrokenAway.close(),
                                ValueToken.of("u"),
                            ),
                            flags=[atf.Flag.UNCERTAIN],
                        )
                    ]
                )
            ]
        ),
    ),
    (
        "{u₂#}",
        LoneDeterminative.of(
            [Determinative.of([Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])])]
        ),
    ),
    (
        "{lu₂@v}",
        LoneDeterminative.of(
            [Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])])]
        ),
    ),
    (
        "{k[i}]",
        LoneDeterminative.of(
            [
                Determinative.of(
                    [
                        Reading.of(
                            (
                                ValueToken.of("k"),
                                BrokenAway.open(),
                                ValueToken.of("i"),
                            )
                        )
                    ]
                ),
                BrokenAway.close(),
            ]
        ),
    ),
    (
        "[{k]i}",
        LoneDeterminative.of(
            [
                BrokenAway.open(),
                Determinative.of(
                    [
                        Reading.of(
                            (
                                ValueToken.of("k"),
                                BrokenAway.close(),
                                ValueToken.of("i"),
                            )
                        )
                    ]
                ),
            ]
        ),
    ),
]

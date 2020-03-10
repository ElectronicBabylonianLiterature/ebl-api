from typing import Sequence

import pytest

from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
    Determinative,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.enclosure_visitor import EnclosureUpdater
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.sign_tokens import (
    Reading,
    Number,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    Token,
    UnknownNumberOfSigns,
    Variant,
    ValueToken,
    Joiner,
)
from ebl.transliteration.domain.word_tokens import Word


def map_line(atf) -> Sequence[Token]:
    line: Line = parse_line(f"1. {atf}")
    visitor = EnclosureUpdater()
    for token in line.content:
        token.accept(visitor)
    return visitor.tokens


@pytest.mark.parametrize(
    "atf, expected",
    [
        ("...", (UnknownNumberOfSigns(frozenset()),)),
        (
            "[...]",
            (
                BrokenAway.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY})),
                BrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.BROKEN_AWAY})
                ),
            ),
        ),
        (
            "(...)",
            (
                PerhapsBrokenAway.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.PERHAPS})),
                PerhapsBrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.PERHAPS})
                ),
            ),
        ),
        (
            "[(...)]",
            (
                BrokenAway.open(),
                PerhapsBrokenAway.open().set_enclosure_type(
                    frozenset({EnclosureType.BROKEN_AWAY})
                ),
                UnknownNumberOfSigns(
                    frozenset(
                        {EnclosureType.BROKEN_AWAY, EnclosureType.PERHAPS_BROKEN_AWAY}
                    )
                ),
                PerhapsBrokenAway.close().set_enclosure_type(
                    frozenset(
                        {EnclosureType.BROKEN_AWAY, EnclosureType.PERHAPS_BROKEN_AWAY}
                    )
                ),
                BrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.BROKEN_AWAY})
                ),
            ),
        ),
        (
            "<(...)>",
            (
                IntentionalOmission.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.INTENTIONAL_OMISSION})),
                IntentionalOmission.close().set_enclosure_type(
                    frozenset({EnclosureType.INTENTIONAL_OMISSION})
                ),
            ),
        ),
        (
            "<...>",
            (
                AccidentalOmission.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.ACCIDENTAL_OMISSION})),
                AccidentalOmission.close().set_enclosure_type(
                    frozenset({EnclosureType.ACCIDENTAL_OMISSION})
                ),
            ),
        ),
        (
            "<<...>>",
            (
                Removal.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.REMOVAL})),
                Removal.close().set_enclosure_type(frozenset({EnclosureType.REMOVAL})),
            ),
        ),
        (
            "{(...)}",
            (
                DocumentOrientedGloss.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                ),
                DocumentOrientedGloss.close().set_enclosure_type(
                    frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                ),
            ),
        ),
        (
            (
                "ku[r ...]",
                (
                    Word.of(
                        (
                            Reading.of(
                                (
                                    ValueToken.of("ku"),
                                    BrokenAway.open(),
                                    ValueToken(
                                        frozenset({EnclosureType.BROKEN_AWAY}), "r"
                                    ),
                                )
                            ),
                        )
                    ),
                    UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY})),
                    BrokenAway.close().set_enclosure_type(
                        frozenset({EnclosureType.BROKEN_AWAY})
                    ),
                ),
            )
        ),
        (
            (
                "{k[ur}-X]",
                (
                    Word.of(
                        (
                            Determinative.of(
                                (
                                    Reading.of(
                                        (
                                            ValueToken.of("k"),
                                            BrokenAway.open(),
                                            ValueToken(
                                                frozenset({EnclosureType.BROKEN_AWAY}),
                                                "ur",
                                            ),
                                        )
                                    ),
                                )
                            ),
                            Joiner.hyphen().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            UnidentifiedSign(frozenset({EnclosureType.BROKEN_AWAY})),
                            BrokenAway.close().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                        ),
                    ),
                ),
            )
        ),
        (
            (
                "ku[r/12[3-x ...]",
                (
                    Word.of(
                        (
                            Variant.of(
                                Reading.of(
                                    (
                                        ValueToken.of("ku"),
                                        BrokenAway.open(),
                                        ValueToken(
                                            frozenset({EnclosureType.BROKEN_AWAY}), "r"
                                        ),
                                    )
                                ),
                                Number.of(
                                    (
                                        ValueToken.of("12"),
                                        BrokenAway.open(),
                                        ValueToken(
                                            frozenset({EnclosureType.BROKEN_AWAY}), "3"
                                        ),
                                    )
                                ),
                            ),
                            Joiner.hyphen().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            UnclearSign(frozenset({EnclosureType.BROKEN_AWAY})),
                        )
                    ),
                    UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY})),
                    BrokenAway.close().set_enclosure_type(
                        frozenset({EnclosureType.BROKEN_AWAY})
                    ),
                ),
            )
        ),
    ],
)
def test_enclosure_type(atf, expected):
    assert map_line(atf) == expected

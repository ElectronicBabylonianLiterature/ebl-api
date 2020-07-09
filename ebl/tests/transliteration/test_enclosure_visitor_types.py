from typing import Sequence

import pytest  # pyre-ignore

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
from ebl.transliteration.domain.sign_tokens import (
    Reading,
    Number,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    UnknownNumberOfSigns,
    Variant,
    ValueToken,
    Joiner,
)
from ebl.transliteration.domain.word_tokens import Word


def map_line(atf) -> Sequence[Token]:
    visitor = EnclosureUpdater()
    parse_line(f"1. {atf}").accept(visitor)
    return visitor.tokens


@pytest.mark.parametrize(
    "atf, expected",
    [
        ("...", (UnknownNumberOfSigns.of(),)),
        (
            "[...]",
            (
                BrokenAway.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY}),
                                     ErasureState.NONE),
                BrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.BROKEN_AWAY})
                ),
            ),
        ),
        (
            "(...)",
            (
                PerhapsBrokenAway.open(),
                UnknownNumberOfSigns(frozenset({EnclosureType.PERHAPS}),
                                     ErasureState.NONE),
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
                UnknownNumberOfSigns.of().set_enclosure_type(
                    frozenset(
                        {EnclosureType.BROKEN_AWAY, EnclosureType.PERHAPS_BROKEN_AWAY}
                    ),
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
                UnknownNumberOfSigns.of().set_enclosure_type(
                    frozenset({EnclosureType.INTENTIONAL_OMISSION})
                ),
                IntentionalOmission.close().set_enclosure_type(
                    frozenset({EnclosureType.INTENTIONAL_OMISSION})
                ),
            ),
        ),
        (
            "<...>",
            (
                AccidentalOmission.open(),
                UnknownNumberOfSigns.of().set_enclosure_type(
                    frozenset({EnclosureType.ACCIDENTAL_OMISSION})
                ),
                AccidentalOmission.close().set_enclosure_type(
                    frozenset({EnclosureType.ACCIDENTAL_OMISSION})
                ),
            ),
        ),
        (
            "<<...>>",
            (
                Removal.open(),
                UnknownNumberOfSigns.of().set_enclosure_type(
                    frozenset({EnclosureType.REMOVAL})
                ),
                Removal.close().set_enclosure_type(frozenset({EnclosureType.REMOVAL})),
            ),
        ),
        (
            "{(...)}",
            (
                DocumentOrientedGloss.open(),
                UnknownNumberOfSigns.of().set_enclosure_type(
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
                                        frozenset({EnclosureType.BROKEN_AWAY}),
                                        ErasureState.NONE,
                                        "r"
                                    ),
                                )
                            ),
                        )
                    ),
                    UnknownNumberOfSigns.of().set_enclosure_type(
                        frozenset({EnclosureType.BROKEN_AWAY})
                    ),
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
                                                ErasureState.NONE,
                                                "ur",
                                            ),
                                        )
                                    ),
                                )
                            ),
                            Joiner.hyphen().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            UnidentifiedSign.of().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
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
                                            frozenset({EnclosureType.BROKEN_AWAY}),
                                            ErasureState.NONE,
                                            "r"
                                        ),
                                    )
                                ),
                                Number.of(
                                    (
                                        ValueToken.of("12"),
                                        BrokenAway.open(),
                                        ValueToken(
                                            frozenset({EnclosureType.BROKEN_AWAY}),
                                            ErasureState.NONE,
                                            "3"
                                        ),
                                    )
                                ),
                            ),
                            Joiner.hyphen().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            UnclearSign.of().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                        )
                    ),
                    UnknownNumberOfSigns.of().set_enclosure_type(
                        frozenset({EnclosureType.BROKEN_AWAY})
                    ),
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

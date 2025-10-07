from typing import Sequence

import pytest

from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Emendation,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
    Determinative,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.enclosure_visitor import EnclosureUpdater
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.sign_tokens import Reading, Number
from ebl.transliteration.domain.tokens import (
    ErasureState,
    LanguageShift,
    Token,
    UnknownNumberOfSigns,
    Variant,
    ValueToken,
    Joiner,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import Word


def map_line(atf) -> Sequence[Token]:
    visitor = EnclosureUpdater()
    parse_line(f"1. {atf}").accept(visitor)
    return visitor.tokens


@pytest.mark.parametrize(
    "atf, expected",
    [
        ("...", (Word.of((UnknownNumberOfSigns.of(),)),)),
        (
            "[...]",
            (
                Word.of(
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(
                            frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE
                        ),
                        BrokenAway.close().set_enclosure_type(
                            frozenset({EnclosureType.BROKEN_AWAY})
                        ),
                    )
                ),
            ),
        ),
        (
            "(...)",
            (
                Word.of(
                    (
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(
                            frozenset({EnclosureType.PERHAPS}), ErasureState.NONE
                        ),
                        PerhapsBrokenAway.close().set_enclosure_type(
                            frozenset({EnclosureType.PERHAPS})
                        ),
                    )
                ),
            ),
        ),
        (
            "[(...)]",
            (
                Word.of(
                    (
                        BrokenAway.open(),
                        PerhapsBrokenAway.open().set_enclosure_type(
                            frozenset({EnclosureType.BROKEN_AWAY})
                        ),
                        UnknownNumberOfSigns.of().set_enclosure_type(
                            frozenset(
                                {
                                    EnclosureType.BROKEN_AWAY,
                                    EnclosureType.PERHAPS_BROKEN_AWAY,
                                }
                            )
                        ),
                        PerhapsBrokenAway.close().set_enclosure_type(
                            frozenset(
                                {
                                    EnclosureType.BROKEN_AWAY,
                                    EnclosureType.PERHAPS_BROKEN_AWAY,
                                }
                            )
                        ),
                        BrokenAway.close().set_enclosure_type(
                            frozenset({EnclosureType.BROKEN_AWAY})
                        ),
                    )
                ),
            ),
        ),
        (
            "<(...)>",
            (
                Word.of(
                    (
                        IntentionalOmission.open(),
                        UnknownNumberOfSigns.of().set_enclosure_type(
                            frozenset({EnclosureType.INTENTIONAL_OMISSION})
                        ),
                        IntentionalOmission.close().set_enclosure_type(
                            frozenset({EnclosureType.INTENTIONAL_OMISSION})
                        ),
                    )
                ),
            ),
        ),
        (
            "<...>",
            (
                Word.of(
                    (
                        AccidentalOmission.open(),
                        UnknownNumberOfSigns.of().set_enclosure_type(
                            frozenset({EnclosureType.ACCIDENTAL_OMISSION})
                        ),
                        AccidentalOmission.close().set_enclosure_type(
                            frozenset({EnclosureType.ACCIDENTAL_OMISSION})
                        ),
                    )
                ),
            ),
        ),
        (
            "<<...>>",
            (
                Word.of(
                    (
                        Removal.open(),
                        UnknownNumberOfSigns.of().set_enclosure_type(
                            frozenset({EnclosureType.REMOVAL})
                        ),
                        Removal.close().set_enclosure_type(
                            frozenset({EnclosureType.REMOVAL})
                        ),
                    )
                ),
            ),
        ),
        (
            "{(...)}",
            (
                DocumentOrientedGloss.open(),
                Word.of(
                    (
                        UnknownNumberOfSigns.of().set_enclosure_type(
                            frozenset({EnclosureType.DOCUMENT_ORIENTED_GLOSS})
                        ),
                    )
                ).set_enclosure_type(
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
                                        "r",
                                    ),
                                )
                            ),
                        )
                    ),
                    Word.of(
                        (
                            UnknownNumberOfSigns.of().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            BrokenAway.close().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                        )
                    ).set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
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
                        )
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
                                            "r",
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
                                            "3",
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
                    Word.of(
                        (
                            UnknownNumberOfSigns.of().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                            BrokenAway.close().set_enclosure_type(
                                frozenset({EnclosureType.BROKEN_AWAY})
                            ),
                        )
                    ).set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
                ),
            )
        ),
        (
            "%n [...]",
            (
                LanguageShift.normalized_akkadian(),
                BrokenAway.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE
                ),
                BrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.BROKEN_AWAY})
                ),
            ),
        ),
        (
            "%n (...)",
            (
                LanguageShift.normalized_akkadian(),
                PerhapsBrokenAway.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.PERHAPS}), ErasureState.NONE
                ),
                PerhapsBrokenAway.close().set_enclosure_type(
                    frozenset({EnclosureType.PERHAPS})
                ),
            ),
        ),
        (
            "%n <...>",
            (
                LanguageShift.normalized_akkadian(),
                Emendation.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
                ),
                Emendation.close().set_enclosure_type(
                    frozenset({EnclosureType.EMENDATION})
                ),
            ),
        ),
        (
            "%n kur-[kur ...]",
            (
                LanguageShift.normalized_akkadian(),
                AkkadianWord.of(
                    (
                        ValueToken.of("kur"),
                        Joiner.hyphen(),
                        BrokenAway.open(),
                        ValueToken(
                            frozenset({EnclosureType.BROKEN_AWAY}),
                            ErasureState.NONE,
                            "kur",
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
        ),
        (
            "%n <... | ...>",
            (
                LanguageShift.normalized_akkadian(),
                Emendation.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
                ),
                MetricalFootSeparator.certain().set_enclosure_type(
                    frozenset({EnclosureType.EMENDATION})
                ),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
                ),
                Emendation.close().set_enclosure_type(
                    frozenset({EnclosureType.EMENDATION})
                ),
            ),
        ),
        (
            "%n <... || ...>",
            (
                LanguageShift.normalized_akkadian(),
                Emendation.open(),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
                ),
                Caesura.certain().set_enclosure_type(
                    frozenset({EnclosureType.EMENDATION})
                ),
                UnknownNumberOfSigns(
                    frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
                ),
                Emendation.close().set_enclosure_type(
                    frozenset({EnclosureType.EMENDATION})
                ),
            ),
        ),
    ],
)
def test_enclosure_type(atf, expected):
    assert map_line(atf) == expected

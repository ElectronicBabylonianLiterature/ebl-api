from ebl.transliteration.domain.signs_transformer import name_arguments


from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.sign_tokens import Reading, Number
from ebl.transliteration.domain.tokens import (
    ErasureState,
    LanguageShift,
    UnknownNumberOfSigns,
    Variant,
    ValueToken,
    Joiner,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import Word

ENCLOSURE_VISITOR_TYPES_CASES_2 = [
    (
        "ku[r/12[3-x ...]",
        (
            Word.of(
                (
                    Variant.of(
                        Reading.of_arguments(
                            name_arguments(
                                (
                                    ValueToken.of("ku"),
                                    BrokenAway.open(),
                                    ValueToken(
                                        frozenset({EnclosureType.BROKEN_AWAY}),
                                        ErasureState.NONE,
                                        "r",
                                    ),
                                )
                            )
                        ),
                        Number.of_arguments(
                            name_arguments(
                                (
                                    ValueToken.of("12"),
                                    BrokenAway.open(),
                                    ValueToken(
                                        frozenset({EnclosureType.BROKEN_AWAY}),
                                        ErasureState.NONE,
                                        "3",
                                    ),
                                ),
                                1,
                                (),
                                (),
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
            UnknownNumberOfSigns(frozenset({EnclosureType.PERHAPS}), ErasureState.NONE),
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
            Caesura.certain().set_enclosure_type(frozenset({EnclosureType.EMENDATION})),
            UnknownNumberOfSigns(
                frozenset({EnclosureType.EMENDATION}), ErasureState.NONE
            ),
            Emendation.close().set_enclosure_type(
                frozenset({EnclosureType.EMENDATION})
            ),
        ),
    ),
]

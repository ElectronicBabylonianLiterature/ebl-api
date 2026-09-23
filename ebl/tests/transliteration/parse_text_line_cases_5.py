from ebl.transliteration.domain.signs_transformer import name_arguments


from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    DocumentOrientedGloss,
    Erasure,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    Word,
)

PARSE_TEXT_LINE_CASES_5 = [
    (
        "1. °me-e-li\\ku°",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Erasure.open(),
                    Word.of(
                        erasure=ErasureState.ERASED,
                        parts=[
                            Reading.of_name("me"),
                            Joiner.hyphen(),
                            Reading.of_name("e"),
                            Joiner.hyphen(),
                            Reading.of_name("li"),
                        ],
                    ),
                    Erasure.center(),
                    Word.of(
                        erasure=ErasureState.OVER_ERASED,
                        parts=[Reading.of_name("ku")],
                    ),
                    Erasure.close(),
                ),
            )
        ],
    ),
    (
        "1. me-e-li-°\\ku°",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
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
            )
        ],
    ),
    (
        "1. °me-e-li\\°-ku",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
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
            )
        ],
    ),
    (
        "1. me-°e\\li°-ku",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("me"),
                            Joiner.hyphen(),
                            Erasure.open(),
                            Reading.of_name("e").set_erasure(ErasureState.ERASED),
                            Erasure.center(),
                            Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                            Erasure.close(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "1. me-°e\\li°-me-°e\\li°-ku",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("me"),
                            Joiner.hyphen(),
                            Erasure.open(),
                            Reading.of_name("e").set_erasure(ErasureState.ERASED),
                            Erasure.center(),
                            Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                            Erasure.close(),
                            Joiner.hyphen(),
                            Reading.of_name("me"),
                            Joiner.hyphen(),
                            Erasure.open(),
                            Reading.of_name("e").set_erasure(ErasureState.ERASED),
                            Erasure.center(),
                            Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                            Erasure.close(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "1. [{(he-pi₂ e]š-šu₂)}",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    BrokenAway.open(),
                    DocumentOrientedGloss.open(),
                    Word.of(
                        parts=[
                            Reading.of_name("he"),
                            Joiner.hyphen(),
                            Reading.of_name("pi", 2),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Reading.of_arguments(
                                name_arguments(
                                    (
                                        ValueToken.of("e"),
                                        BrokenAway.close(),
                                        ValueToken.of("š"),
                                    )
                                )
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("šu", 2),
                        ]
                    ),
                    DocumentOrientedGloss.close(),
                ),
            )
        ],
    ),
]

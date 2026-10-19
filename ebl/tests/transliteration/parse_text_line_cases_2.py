from ebl.transliteration.domain.signs_transformer import name_arguments


from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    CommentaryProtocol,
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import (
    Word,
)

PARSE_TEXT_LINE_CASES_2 = [
    (
        "1. |GAL|",
        [
            TextLine.of_iterable(
                LineNumber(1), (Word.of([CompoundGrapheme.of(["GAL"])]),)
            )
        ],
    ),
    (
        "1. !qt !bs !cm !zz",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    CommentaryProtocol.of("!qt"),
                    CommentaryProtocol.of("!bs"),
                    CommentaryProtocol.of("!cm"),
                    CommentaryProtocol.of("!zz"),
                ),
            )
        ],
    ),
    (
        "1. x X x?# X#!",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of([UnclearSign.of()]),
                    Word.of([UnidentifiedSign.of()]),
                    Word.of([UnclearSign.of([atf.Flag.UNCERTAIN, atf.Flag.DAMAGE])]),
                    Word.of(
                        [UnidentifiedSign.of([atf.Flag.DAMAGE, atf.Flag.CORRECTION])]
                    ),
                ),
            )
        ],
    ),
    (
        "1. x-ti ti-X",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of([UnclearSign.of(), Joiner.hyphen(), Reading.of_name("ti")]),
                    Word.of(
                        [
                            Reading.of_name("ti"),
                            Joiner.hyphen(),
                            UnidentifiedSign.of(),
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of((BrokenAway.open(), UnknownNumberOfSigns.of())),
                    Word.of(
                        parts=[
                            Reading.of_arguments(
                                name_arguments(
                                    (
                                        ValueToken.of("r"),
                                        BrokenAway.close(),
                                        ValueToken.of("u"),
                                    ),
                                    flags=[atf.Flag.UNCERTAIN],
                                )
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("u", 2),
                            Joiner.hyphen(),
                            Reading.of_name("qu"),
                        ]
                    ),
                    Word.of(
                        parts=[
                            Reading.of_name("na"),
                            Joiner.hyphen(),
                            Reading.of_arguments(
                                name_arguments(
                                    (
                                        ValueToken.of("a"),
                                        BrokenAway.open(),
                                        ValueToken.of("n"),
                                    )
                                )
                            ),
                            Joiner.hyphen(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("ši"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            Reading.of_name("ku"),
                            Joiner.hyphen(),
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                        ]
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(3),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                        ]
                    ),
                ),
            ),
        ],
    ),
    (
        "1. [...]-qa-[...]-ba-[...]\n2. pa-[...]",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        parts=[
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("qa"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("ba"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2),
                (
                    Word.of(
                        parts=[
                            Reading.of_name("pa"),
                            Joiner.hyphen(),
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                ),
            ),
        ],
    ),
]

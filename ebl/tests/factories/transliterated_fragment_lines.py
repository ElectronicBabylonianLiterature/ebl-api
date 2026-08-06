from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    WordOmitted,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import InWordNewline, Word


FIRST_TEXT_LINES = (
    TextLine.of_iterable(
        LineNumber(1, True),
        (
            Word.of([UnidentifiedSign.of()]),
            Word.of(
                [
                    Logogram.of_name(
                        "BA",
                        surrogate=[
                            Reading.of_name("ku"),
                            Joiner.hyphen(),
                            Reading.of_name("u", 4),
                        ],
                    )
                ]
            ),
            Column.of(),
            WordOmitted.of(),
            Tabulation.of(),
            Word.of(
                [
                    BrokenAway.open(),
                    UnknownNumberOfSigns.of(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                    BrokenAway.close(),
                    Joiner.hyphen(),
                    Reading.of_name("nu"),
                    Joiner.hyphen(),
                    Reading.of_name("ši"),
                ]
            ),
            Variant.of(Divider.of(":"), Reading.of_name("ku")),
            Word.of(
                [
                    BrokenAway.open(),
                    UnknownNumberOfSigns.of(),
                    BrokenAway.close(),
                ]
            ),
            Column.of(2),
            Divider.of(":", ("@v",), (Flag.DAMAGE,)),
            CommentaryProtocol.of("!qt"),
            Word.of([Number.of_name("10", flags=[Flag.DAMAGE])]),
        ),
    ),
    TextLine.of_iterable(
        LineNumber(2, True),
        (
            Word.of(
                [
                    BrokenAway.open(),
                    UnknownNumberOfSigns.of(),
                    BrokenAway.close(),
                ]
            ),
            Word.of([Logogram.of_name("GI", 6)]),
            Word.of([Reading.of_name("ana")]),
            Word.of(
                [
                    Reading.of_name("u", 4),
                    Joiner.hyphen(),
                    Reading.of(
                        (
                            ValueToken.of("š"),
                            BrokenAway.open(),
                            ValueToken.of("u"),
                        )
                    ),
                ]
            ),
            Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
        ),
    ),
    TextLine.of_iterable(
        LineNumber(3, True),
        (
            Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
            Word.of(
                [
                    Reading.of(
                        (
                            ValueToken.of("k"),
                            BrokenAway.close(),
                            ValueToken.of("i"),
                        )
                    ),
                    Joiner.hyphen(),
                    Reading.of_name("du"),
                ]
            ),
            Word.of([Reading.of_name("u")]),
            Word.of(
                [
                    Reading.of_name("ba"),
                    Joiner.hyphen(),
                    Reading.of_name("ma"),
                    Joiner.hyphen(),
                    Reading.of(
                        (
                            ValueToken.of("t"),
                            BrokenAway.open(),
                            ValueToken.of("i"),
                        )
                    ),
                ]
            ),
            Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
        ),
    ),
    TextLine.of_iterable(
        LineNumber(6, True),
        (
            Word.of(
                [
                    BrokenAway.open(),
                    UnknownNumberOfSigns.of(),
                    BrokenAway.close(),
                ]
            ),
            Word.of([UnclearSign.of([Flag.DAMAGE])]),
            Word.of([Reading.of_name("mu")]),
            Word.of(
                [
                    Reading.of_name("ta"),
                    Joiner.hyphen(),
                    Reading.of_name("ma"),
                    InWordNewline.of(),
                    Joiner.hyphen(),
                    Reading.of_name("tu", 2),
                ]
            ),
        ),
    ),
)

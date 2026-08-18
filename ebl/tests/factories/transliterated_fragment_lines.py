from ebl.tests.factories.first_text_line import FIRST_TEXT_LINE
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Logogram,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import InWordNewline, Word


FIRST_TEXT_LINES = (
    FIRST_TEXT_LINE,
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

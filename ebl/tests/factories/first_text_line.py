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
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnidentifiedSign
from ebl.transliteration.domain.word_tokens import Word


FIRST_TEXT_LINE = TextLine.of_iterable(
    LineNumber(1, True),
    (
        Word.of([UnidentifiedSign.of()]),
        Word.of(
            [
                Logogram.of_name("BA").with_surrogate(
                    [
                        Reading.of_name("ku"),
                        Joiner.hyphen(),
                        Reading.of_name("u", 4),
                    ]
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
)

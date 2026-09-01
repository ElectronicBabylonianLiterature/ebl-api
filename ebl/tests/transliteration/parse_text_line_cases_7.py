from ebl.transliteration.domain import atf
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Column,
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
)
from ebl.transliteration.domain.word_tokens import (
    Word,
)
from ebl.tests.transliteration.parse_text_line_fixtures import (
    create_number_part,
)

PARSE_TEXT_LINE_CASES_7 = [
    (
        "1. ... -ad ad- ... ad- ... -ad",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(
                        (
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            Reading.of_name("ad"),
                        )
                    ),
                    Word.of(
                        (
                            Reading.of_name("ad"),
                            Joiner.hyphen(),
                            UnknownNumberOfSigns.of(),
                        )
                    ),
                    Word.of(
                        (
                            Reading.of_name("ad"),
                            Joiner.hyphen(),
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            Reading.of_name("ad"),
                        )
                    ),
                ),
            )
        ],
    ),
    (
        "1. %grc ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    LanguageShift.of("%grc"),
                    GreekWord.of(
                        [
                            GreekLetter.of(letter)
                            for letter in (
                                "ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω"
                            )
                        ]
                    ),
                ),
            )
        ],
    ),
    (
        "1. %akkgrc α",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    LanguageShift.of("%akkgrc"),
                    GreekWord.of([GreekLetter.of("α")], Language.AKKADIAN),
                ),
            )
        ],
    ),
    (
        "1. %suxgrc ε",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    LanguageShift.of("%suxgrc"),
                    GreekWord.of([GreekLetter.of("ε")], Language.SUMERIAN),
                ),
            )
        ],
    ),
    (
        "1. %grc &2 α & ε",
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    LanguageShift.of("%grc"),
                    Column.of(2),
                    GreekWord.of([GreekLetter.of("α")]),
                    Column.of(),
                    GreekWord.of([GreekLetter.of("ε")]),
                ),
            )
        ],
    ),
    (
        "42. 1;23.45",
        [
            TextLine.of_iterable(
                LineNumber(42),
                (
                    Word.of(
                        [
                            create_number_part("1"),
                            Joiner.of(atf.Joiner.SEMICOLON),
                            create_number_part("23"),
                            Joiner.of(atf.Joiner.DOT),
                            create_number_part("45"),
                        ]
                    ),
                ),
            )
        ],
    ),
]

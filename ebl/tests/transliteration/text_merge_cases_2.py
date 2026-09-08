from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import EmphasisPart, LanguagePart, StringPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word

TEXT_MERGE_CASES_2 = [
    (
        Text.of_iterable(
            [TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])])]
        ),
        Text.of_iterable(
            [TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])])]
        ),
        Text.of_iterable(
            [TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])])]
        ),
    ),
    (
        Text.of_iterable([NoteLine((StringPart("this is a note "),))]),
        Text.of_iterable([NoteLine((StringPart("this is another note "),))]),
        Text.of_iterable([NoteLine((StringPart("this is another note "),))]),
    ),
    (
        Text.of_iterable([NoteLine((StringPart("this is a note "),))]),
        Text.of_iterable([NoteLine((EmphasisPart("this is a note "),))]),
        Text.of_iterable([NoteLine((EmphasisPart("this is a note "),))]),
    ),
    (
        Text.of_iterable(
            [
                NoteLine(
                    (
                        LanguagePart.of_transliteration(
                            Language.AKKADIAN, (ValueToken.of("bu"),)
                        ),
                    )
                )
            ]
        ),
        Text.of_iterable(
            [
                NoteLine(
                    (
                        LanguagePart.of_transliteration(
                            Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                        ),
                    )
                )
            ]
        ),
        Text.of_iterable(
            [
                NoteLine(
                    (
                        LanguagePart.of_transliteration(
                            Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                        ),
                    )
                )
            ]
        ),
    ),
]

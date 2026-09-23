from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.tests.corpus.chapter_merge_fixtures import (
    LEMMATIZED_MANUSCRIPT_LINE,
    IS_BEGINNING_OF_SECTION,
    IS_SECOND_LINE_OF_PARALLELISM,
    LABELS,
    LINE,
    MANUSCRIPT_ID,
    MANUSCRIPT_LINE,
    NEW_TEXT_LINE,
    NOTE,
    OLD_LINE_NUMBERS,
    RECONSTRUCTION,
    TEXT_LINE,
)

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

LEMMATIZED_MANUSCRIPT_LINES = (LEMMATIZED_MANUSCRIPT_LINE,)


def unchanged(old, new):
    """A merge whose result is the new value itself."""
    return (old, new, new)


CHAPTER_MERGE_CASES_2_1 = [
    unchanged(
        LINE,
        LINE,
    ),
    (
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    LEMMATIZED_MANUSCRIPT_LINES,
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(2),
            (
                LineVariant(
                    (
                        AkkadianWord.of((ValueToken.of("kur"),)),
                        AkkadianWord.of((ValueToken.of("ra"),)),
                    ),
                    NOTE,
                    (
                        ManuscriptLine(
                            MANUSCRIPT_ID,
                            LABELS,
                            TextLine(
                                LineNumber(1),
                                (
                                    Word.of(
                                        [
                                            Reading.of_arguments(
                                                name_arguments(
                                                    [
                                                        ValueToken.of("ku"),
                                                        BrokenAway.close(),
                                                    ]
                                                )
                                            ),
                                            Joiner.hyphen(),
                                            Reading.of_name("nu"),
                                            Joiner.hyphen(),
                                            Reading.of_name("si"),
                                        ]
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(2),
            (
                LineVariant(
                    (
                        AkkadianWord.of((ValueToken.of("kur"),)),
                        AkkadianWord.of((ValueToken.of("ra"),)),
                    ),
                    NOTE,
                    LEMMATIZED_MANUSCRIPT_LINES,
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
    ),
    (
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(2),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    (ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),),
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(2),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    (
                        ManuscriptLine(
                            MANUSCRIPT_ID, LABELS, TEXT_LINE.merge(NEW_TEXT_LINE)
                        ),
                    ),
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
    ),
]

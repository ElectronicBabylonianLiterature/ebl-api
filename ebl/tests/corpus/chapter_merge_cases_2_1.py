from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.tests.corpus.chapter_merge_fixtures import (
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
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

CHAPTER_MERGE_CASES_2_1 = [
    (LINE, LINE, LINE),
    (
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION,
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
                                        ],
                                        unique_lemma=(WordId("word"),),
                                        alignment=0,
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
                                        ],
                                        unique_lemma=(WordId("word"),),
                                        alignment=0,
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

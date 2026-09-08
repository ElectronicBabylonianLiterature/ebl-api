from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.tests.corpus.chapter_merge_fixtures import (
    IS_BEGINNING_OF_SECTION,
    IS_SECOND_LINE_OF_PARALLELISM,
    LABELS,
    MANUSCRIPT_ID,
    MANUSCRIPT_LINE,
    NEW_TEXT_LINE,
    NOTE,
    OLD_LINE_NUMBERS,
    RECONSTRUCTION,
    RECONSTRUCTION_WITHOUT_LEMMA,
    TEXT_LINE,
)

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import Caesura
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

CHAPTER_MERGE_CASES_2_2 = [
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
                        MANUSCRIPT_LINE,
                    ),
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    (
                        ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                        ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
                    ),
                ),
            ),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    (
                        ManuscriptLine(MANUSCRIPT_ID, LABELS, NEW_TEXT_LINE),
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
    (
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NOTE, ()),),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NOTE, ()),),
            OLD_LINE_NUMBERS,
            True,
            True,
        ),
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NOTE, ()),),
            OLD_LINE_NUMBERS,
            True,
            True,
        ),
    ),
    (
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NoteLine((StringPart("a note"),)), ()),),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NoteLine((StringPart("new note"),)), ()),),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
        Line(
            LineNumber(1),
            (LineVariant(RECONSTRUCTION, NoteLine((StringPart("new note"),)), ()),),
            OLD_LINE_NUMBERS,
            IS_SECOND_LINE_OF_PARALLELISM,
            IS_BEGINNING_OF_SECTION,
        ),
    ),
    (
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION),)),
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION_WITHOUT_LEMMA),)),
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION),)),
    ),
    (
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)),
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION_WITHOUT_LEMMA,
                    None,
                    (MANUSCRIPT_LINE.update_alignments([]),),
                ),
            ),
        ),
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)),
    ),
    (
        Line(LineNumber(1), (LineVariant(RECONSTRUCTION, None, (MANUSCRIPT_LINE,)),)),
        Line(
            LineNumber(1),
            (
                LineVariant(
                    (Caesura.certain(),),
                    None,
                    (MANUSCRIPT_LINE.update_alignments([]),),
                ),
            ),
        ),
        Line(
            LineNumber(1),
            (
                LineVariant(
                    (Caesura.certain(),),
                    None,
                    (MANUSCRIPT_LINE.update_alignments([None]),),
                ),
            ),
        ),
    ),
]

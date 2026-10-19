from ebl.tests.corpus.chapter_merge_fixtures import (
    LEMMATIZED_MANUSCRIPT_LINE,
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
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import Caesura
from ebl.transliteration.domain.note_line import NoteLine


def unchanged(old, new):
    """A merge whose result is the new value itself."""
    return (old, new, new)


CHAPTER_MERGE_CASES_2_2 = [
    (
        Line(
            LineNumber(1),
            (
                LineVariant(
                    RECONSTRUCTION,
                    NOTE,
                    (
                        LEMMATIZED_MANUSCRIPT_LINE,
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
    unchanged(
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
    ),
    unchanged(
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

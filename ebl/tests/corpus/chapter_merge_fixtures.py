import attr

from ebl.transliteration.domain.text_id import TextId
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Manuscript
from ebl.common.domain.stage import Stage
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.genre import Genre


MANUSCRIPT_ID = 1


LABELS = (ColumnLabel.from_int(1),)


TEXT_LINE = TextLine(
    LineNumber(1),
    (
        Word.of([Reading.of_name("kur")], unique_lemma=(WordId("word1"),), alignment=0),
        Word.of(
            [Reading.of_name("ra")], unique_lemma=(WordId("word2"),), alignment=None
        ),
    ),
)


NEW_MANUSCRIPT_ID = 2


NEW_LABELS = (SurfaceLabel.from_label(Surface.REVERSE),)


NEW_TEXT_LINE = TextLine(
    LineNumber(1), (Word.of([Reading.of_name("kur")]), Word.of([Reading.of_name("pa")]))
)


MANUSCRIPT_LINE = ManuscriptLine(MANUSCRIPT_ID, LABELS, TEXT_LINE)


RECONSTRUCTION = (
    AkkadianWord.of((ValueToken.of("buāru"),), unique_lemma=(WordId("buāru I"),)),
)


RECONSTRUCTION_WITHOUT_LEMMA = (AkkadianWord.of((ValueToken.of("buāru"),)),)


IS_SECOND_LINE_OF_PARALLELISM = True


IS_BEGINNING_OF_SECTION = True


NOTE = None


OLD_LINE_NUMBERS = ()


LINE = Line(
    LineNumber(1),
    (LineVariant(RECONSTRUCTION, NOTE, (MANUSCRIPT_LINE,)),),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


TEXT_ID = TextId(Genre.LITERATURE, 0, 0)


CLASSIFICATION = Classification.ANCIENT


STAGE = Stage.NEO_BABYLONIAN


VERSION = "A"


CHAPTER_NAME = "I"


ORDER = 1


MANUSCRIPT = Manuscript(MANUSCRIPT_ID)


MUSEUM_NUMBER = MuseumNumber.of("K.1")


CHAPTER = Chapter(
    TEXT_ID,
    CLASSIFICATION,
    STAGE,
    VERSION,
    CHAPTER_NAME,
    ORDER,
    (MANUSCRIPT,),
    (MUSEUM_NUMBER,),
    (LINE,),
)


NEW_CLASSIFICATION = Classification.MODERN


NEW_STAGE = Stage.MIDDLE_ASSYRIAN


NEW_VERSION = "B"


NEW_CHAPTER_NAME = "II"


NEW_ORDER = 2


NEW_MANUSCRIPT = Manuscript(2, siglum_disambiguator="b")


NOTE = NoteLine((StringPart("a note"),))


NEW_LINE = Line(
    LineNumber(1),
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
)


ANOTHER_NEW_LINE = Line(
    LineNumber(2),
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    attr.evolve(NEW_TEXT_LINE, line_number=LineNumber(2)),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


NEW_PARATEXT = Line(
    LineNumber(1),
    (
        LineVariant(
            RECONSTRUCTION,
            NOTE,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    TEXT_LINE,
                    (NoteLine((StringPart("paratext"),)),),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)


OLD_LINE = Line(
    LineNumber(2),
    (
        LineVariant(
            (),
            None,
            (
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    attr.evolve(TEXT_LINE, line_number=LineNumber(2)),
                ),
            ),
        ),
    ),
    OLD_LINE_NUMBERS,
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
)

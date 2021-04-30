import attr

from ebl.corpus.domain.chapter import Chapter, TextLineEntry
from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word

MANUSCRIPT_ID = 9001
COLOPHON = Transliteration.of_iterable(
    [EmptyLine(), TextLine(LineNumber(1, True), (Word.of([Reading.of_name("ku")]),))]
)
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
MANUSCRIPT_TEXT_1 = TextLine(
    LineNumber(1), (Word.of([Reading.of([ValueToken.of("ku")])]),)
)

LINE_VARIANT_1 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (ManuscriptLine(MANUSCRIPT_ID, tuple(), MANUSCRIPT_TEXT_1),),
)
LINE_1 = Line(LineNumber(1), (LINE_VARIANT_1,))

LINE_VARIANT_2 = LineVariant(
    LINE_RECONSTRUCTION, None, (ManuscriptLine(MANUSCRIPT_ID, tuple(), EmptyLine()),)
)
LINE_2 = Line(LineNumber(2), (LINE_VARIANT_2,))

MANUSCRIPT_TEXT_3 = attr.evolve(MANUSCRIPT_TEXT_1, line_number=LineNumber(3))
LINE_VARIANT_3 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (ManuscriptLine(MANUSCRIPT_ID, tuple(), MANUSCRIPT_TEXT_3),),
)
LINE_3 = Line(LineNumber(3), (LINE_VARIANT_3,))

SIGNS = ("FOO BAR",)
CHAPTER = Chapter(
    TextId(0, 0),
    manuscripts=(Manuscript(MANUSCRIPT_ID, colophon=COLOPHON),),
    lines=(LINE_1, LINE_2, LINE_3),
    signs=SIGNS,
)


def test_signs() -> None:
    assert CHAPTER.signs == SIGNS


def test_text_lines() -> None:
    assert CHAPTER.text_lines == [
        [
            TextLineEntry(MANUSCRIPT_TEXT_1, 0),
            TextLineEntry(MANUSCRIPT_TEXT_3, 2),
            *[TextLineEntry(line, None) for line in COLOPHON.text_lines],
        ]
    ]

import attr
from ebl.corpus.domain.chapter import Chapter, Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
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
MANUSCRIPT_TEXT = TextLine(
    LineNumber(1), (Word.of([Reading.of([ValueToken.of("ku")])]),)
)

LINE_VARIANT_1 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (ManuscriptLine(MANUSCRIPT_ID, tuple(), MANUSCRIPT_TEXT),),
)
LINE_1 = Line(LineNumber(1), (LINE_VARIANT_1,))

LINE_VARIANT_2 = LineVariant(
    LINE_RECONSTRUCTION, None, (ManuscriptLine(MANUSCRIPT_ID, tuple(), EmptyLine()),)
)
LINE_2 = Line(LineNumber(2), (LINE_VARIANT_2,))

LINE_VARIANT_3 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (
        ManuscriptLine(
            MANUSCRIPT_ID,
            tuple(),
            attr.evolve(MANUSCRIPT_TEXT, line_number=LineNumber(3)),
        ),
    ),
)
LINE_3 = Line(LineNumber(3), (LINE_VARIANT_3,))

SIGNS = ("FOO BAR",)
CHAPTER = Chapter(
    manuscripts=(Manuscript(MANUSCRIPT_ID, colophon=COLOPHON),),
    lines=(LINE_1, LINE_2, LINE_3),
    signs=SIGNS,
)


def test_signs() -> None:
    assert CHAPTER.signs == SIGNS


def test_manuscript_text_lines() -> None:
    assert CHAPTER.get_manuscript_text_lines(0) == [
        LINE_VARIANT_1.manuscripts[0].line,
        LINE_VARIANT_3.manuscripts[0].line,
        *COLOPHON.text_lines,
    ]

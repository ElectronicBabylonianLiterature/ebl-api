from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.atf import Surface
from ebl.corpus.web.extant_lines import ExtantLinesSchema
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema


LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
MANUSCRIPT_TEXT_1 = TextLine(
    LineNumber(2), (Word.of([Reading.of([ValueToken.of("ku")])]),)
)


def test_extant_lines_schema() -> None:
    manuscript = Manuscript(1)
    manuscript_line = ManuscriptLine(1, LABELS, MANUSCRIPT_TEXT_1)
    variant = LineVariant((), manuscripts=(manuscript_line,))
    text_line = Line(LineNumber(1), (variant,))
    chapter = Chapter(
        TextId(Genre.LITERATURE, 0, 0), manuscripts=(manuscript,), lines=(text_line,)
    )
    assert ExtantLinesSchema().dump(chapter) == {
        "extantLines": {
            str(manuscript.siglum): {
                " ".join(label.to_value() for label in manuscript_line.labels): [
                    {
                        "isSideBoundary": False,
                        "lineNumber": OneOfLineNumberSchema().dump(text_line.number),
                    }
                ]
            }
        }
    }

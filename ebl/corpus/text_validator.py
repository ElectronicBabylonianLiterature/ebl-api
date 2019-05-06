from ebl.corpus.text import Chapter, TextVisitor, Manuscript, Line, \
    ManuscriptLine
from ebl.errors import DataError
from ebl.fragment.transliteration import Transliteration, TransliterationError
from ebl.fragmentarium.validator import Validator
from ebl.text.labels import LineNumberLabel


def invalid_atf(chapter: Chapter,
                line_number: LineNumberLabel,
                manuscript_id: int) -> Exception:
    siglum = [manuscript.siglum
              for manuscript in chapter.manuscripts
              if manuscript.id == manuscript_id][0]
    return DataError(
        f'Invalid transliteration on'
        f' line {line_number.to_value()}'
        f' manuscript {siglum}.'
    )


class TextValidator(TextVisitor):

    def __init__(self, bibliography, sign_list):
        self._bibliography = bibliography
        self._sign_list = sign_list
        self._chapter = None
        self._line = None

    def visit_chapter(self, chapter: Chapter) -> None:
        self._chapter = chapter

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        self._bibliography.validate_references(manuscript.references)

    def visit_line(self, line: Line) -> None:
        self._line = line

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        try:
            Validator(Transliteration(manuscript_line.line.atf)
                      .with_signs(self._sign_list)).validate()
        except TransliterationError:
            raise invalid_atf(self._chapter,
                              self._line.number,
                              manuscript_line.manuscript_id)

from collections import Counter
from functools import singledispatchmethod  # type: ignore

from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, \
    TextVisitor
from ebl.errors import DataError
from ebl.transliteration.domain.alignment import AlignmentError
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.tokens import Token, TokenVisitor
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError
from ebl.transliteration.domain.word_tokens import Word


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


class AlignmentVisitor(TokenVisitor):

    def __init__(self):
        self.alignments = []

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        pass

    @visit.register
    def _visit_word(self, word: Word) -> None:
        if word.alignment is not None:
            self.alignments.append(word.alignment)

    def validate(self):
        if any(count > 1 for _, count in Counter(self.alignments).items()):
            raise AlignmentError()


class TextValidator(TextVisitor):

    def __init__(self, bibliography, transliteration_factory):
        super().__init__(TextVisitor.Order.PRE)
        self._bibliography = bibliography
        self._transliteration_factory = transliteration_factory
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
            self._transliteration_factory.create(manuscript_line.line.atf)
        except TransliterationError:
            raise invalid_atf(self._chapter,
                              self._line.number,
                              manuscript_line.manuscript_id)

        alignment_validator = AlignmentVisitor()
        for token in manuscript_line.line.content:
            token.accept(alignment_validator)
        alignment_validator.validate()

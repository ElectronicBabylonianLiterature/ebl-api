from typing import Optional
from collections import Counter

from ebl.corpus.domain.chapter import Chapter, Line, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.ordered import Order
from ebl.corpus.domain.text_visitor import TextVisitor
from ebl.errors import DataError, Defect
from ebl.transliteration.domain.alignment import AlignmentError
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.tokens import TokenVisitor
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import Word


def invalid_atf(
    chapter: Chapter, line_number: AbstractLineNumber, manuscript_id: int
) -> Exception:
    siglum = [
        manuscript.siglum
        for manuscript in chapter.manuscripts
        if manuscript.id == manuscript_id
    ][0]
    return DataError(
        f"Invalid transliteration on"
        f" line {line_number.atf}"
        f" manuscript {siglum}."
    )


class AlignmentVisitor(TokenVisitor):
    def __init__(self):
        self.alignments = []

    def visit_word(self, word: Word) -> None:
        if word.alignment is not None:
            self.alignments.append(word.alignment)

    def validate(self):
        if any(count > 1 for _, count in Counter(self.alignments).items()):
            raise AlignmentError()


class TextValidator(TextVisitor):
    def __init__(self, bibliography, transliteration_factory):
        super().__init__(Order.PRE)
        self._bibliography = bibliography
        self._transliteration_factory = transliteration_factory
        self._chapter: Optional[Chapter] = None
        self._line: Optional[Line] = None

    @property
    def line(self) -> Line:
        if self._line is None:
            raise Defect("Trying to access line before a line was visited.")

        return self._line  # pyre-ignore[7]

    @property
    def chapter(self) -> Chapter:
        if self._chapter is None:
            raise Defect("Trying to access chapter before a chapter was visited.")

        return self._chapter  # pyre-ignore[7]

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
            raise invalid_atf(
                self.chapter, self.line.number, manuscript_line.manuscript_id
            )

        alignment_validator = AlignmentVisitor()
        manuscript_line.line.accept(alignment_validator)
        alignment_validator.validate()

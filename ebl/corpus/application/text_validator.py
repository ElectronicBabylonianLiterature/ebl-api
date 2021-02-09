from typing import Optional, cast

import pydash  # pyre-ignore[21]
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.corpus.domain.chapter import Chapter, Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text import Text, TextItem, TextVisitor
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
        if pydash.duplicates(self.alignments):
            raise AlignmentError()


class TextValidator(TextVisitor):
    def __init__(self, bibliography, transliteration_factory):
        self._bibliography = bibliography
        self._transliteration_factory = transliteration_factory
        self._chapter: Optional[Chapter] = None
        self._line: Optional[Line] = None

    @property
    def line(self) -> Line:
        if self._line is None:
            raise Defect("Trying to access line before a line was visited.")

        return cast(Line, self._line)

    @property
    def chapter(self) -> Chapter:
        if self._chapter is None:
            raise Defect("Trying to access chapter before a chapter was visited.")

        return cast(Chapter, self._chapter)

    @singledispatchmethod  # pyre-ignore[56]
    def visit(self, item: TextItem) -> None:
        pass

    @visit.register(Text)  # pyre-ignore[56]
    def _visit_text(self, text: Text) -> None:
        for chapter in text.chapters:
            self.visit(chapter)

    @visit.register(Chapter)  # pyre-ignore[56]
    def _visit_chapter(self, chapter: Chapter) -> None:
        self._chapter = chapter

        for manuscript in chapter.manuscripts:
            self.visit(manuscript)

        for line in chapter.lines:
            self.visit(line)

    @visit.register(Manuscript)  # pyre-ignore[56]
    def _visit_manuscript(self, manuscript: Manuscript) -> None:
        self._bibliography.validate_references(manuscript.references)

    @visit.register(Line)  # pyre-ignore[56]
    def _visit_line(self, line: Line) -> None:
        self._line = line
        for variant in line.variants:
            self.visit(variant)

    @visit.register(LineVariant)  # pyre-ignore[56]
    def _visit_line_variant(self, variant: LineVariant) -> None:
        for manuscript_line in variant.manuscripts:
            self.visit(manuscript_line)

    @visit.register(ManuscriptLine)  # pyre-ignore[56]
    def _visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        try:
            self._transliteration_factory.create(manuscript_line.line.atf)
        except TransliterationError:
            raise invalid_atf(
                self.chapter, self.line.number, manuscript_line.manuscript_id
            )

        alignment_validator = AlignmentVisitor()
        manuscript_line.line.accept(alignment_validator)
        alignment_validator.validate()

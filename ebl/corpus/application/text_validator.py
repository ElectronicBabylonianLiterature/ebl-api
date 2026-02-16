from functools import singledispatchmethod
from typing import Optional

import pydash

from ebl.corpus.domain.chapter import (
    Chapter,
    ChapterItem,
    ChapterVisitor,
    TextLineEntry,
)
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Siglum
from ebl.errors import DataError, Defect
from ebl.transliteration.domain.alignment import AlignmentError
from ebl.transliteration.domain.greek_tokens import GreekWord
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.tokens import TokenVisitor
from ebl.transliteration.domain.word_tokens import Word


def data_error(
    source: Exception,
    chapter: Chapter,
    line_number: AbstractLineNumber,
    manuscript_id: int,
) -> Exception:
    siglum = [
        manuscript.siglum
        for manuscript in chapter.manuscripts
        if manuscript.id == manuscript_id
    ][0]
    return DataError(f"Invalid line {line_number.atf} {siglum}. {source}")


class AlignmentVisitor(TokenVisitor):
    def __init__(self):
        self.alignments = []

    def visit_word(self, word: Word) -> None:
        if word.alignment is not None:
            self.alignments.append(word.alignment)

    def visit_greek_word(self, word: GreekWord) -> None:
        if word.alignment is not None:
            self.alignments.append(word.alignment)

    def validate(self):
        if duplicates := pydash.duplicates(self.alignments):
            raise AlignmentError(duplicates)


def create_error_message(siglum: Siglum, entry: TextLineEntry, chapter: Chapter) -> str:
    return (
        f"{siglum} colophon {entry.line.atf}"
        if entry.source is None
        else f"{chapter.lines[entry.source].number.atf} {siglum} {entry.line.atf}"
    )


class TextValidator(ChapterVisitor):
    def __init__(self):
        self._chapter: Optional[Chapter] = None
        self._line: Optional[Line] = None

    @property
    def line(self) -> Line:
        if self._line is None:
            raise Defect("Trying to access line before a line was visited.")

        return self._line

    @property
    def chapter(self) -> Chapter:
        if self._chapter is None:
            raise Defect("Trying to access chapter before a chapter was visited.")

        return self._chapter

    @singledispatchmethod
    def visit(self, item: ChapterItem) -> None:
        pass

    @visit.register(Chapter)
    def _visit_chapter(self, chapter: Chapter) -> None:
        self._chapter = chapter

        for manuscript in chapter.manuscripts:
            self.visit(manuscript)

        for line in chapter.lines:
            self.visit(line)

        if invalid_lines := [
            create_error_message(siglum, entry, chapter)
            for siglum, entry in chapter.invalid_lines
        ]:
            raise DataError(f"Invalid signs on lines: {', '.join(invalid_lines)}.")

    @visit.register(Line)
    def _visit_line(self, line: Line) -> None:
        self._line = line
        for variant in line.variants:
            self.visit(variant)

    @visit.register(LineVariant)
    def _visit_line_variant(self, variant: LineVariant) -> None:
        for manuscript_line in variant.manuscripts:
            self.visit(manuscript_line)

    @visit.register(ManuscriptLine)
    def _visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        try:
            alignment_validator = AlignmentVisitor()
            manuscript_line.line.accept(alignment_validator)
            alignment_validator.validate()
        except AlignmentError as error:
            raise data_error(
                error, self.chapter, self.line.number, manuscript_line.manuscript_id
            ) from error

from functools import singledispatchmethod
from typing import List

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.domain.chapter import Chapter, ChapterItem
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.transliteration.domain.alignment import AlignmentError


class AlignmentUpdater(ChapterUpdater):
    def __init__(self, alignment: Alignment):
        super().__init__()
        self._alignment = alignment
        self._lines: List[Line] = []
        self._variants: List[LineVariant] = []
        self._manuscript_lines: List[ManuscriptLine] = []

    @property
    def line_index(self) -> int:
        return len(self._lines)

    @property
    def variant_index(self) -> int:
        return len(self._variants)

    @property
    def manuscript_line_index(self) -> int:
        return len(self._manuscript_lines)

    @property
    def current_alignment(self) -> ManuscriptLineAlignment:
        try:
            return self._alignment.get_manuscript_line(
                self.line_index, self.variant_index, self.manuscript_line_index
            )
        except IndexError:
            alignment_index = [
                self.line_index,
                self.variant_index,
                self.manuscript_line_index,
            ]
            raise AlignmentError(f"Invalid alignment index {alignment_index}.")

    @singledispatchmethod
    def visit(self, item: ChapterItem) -> None:
        super().visit(item)

    @visit.register(Line)
    def _visit_line(self, line: Line) -> None:
        alignment_variants = self._alignment.get_number_of_variants(self.line_index)
        line_variants = len(line.variants)
        if alignment_variants != line_variants:
            raise AlignmentError(
                "Invalid number of variants. "
                f"Got {alignment_variants}, expected {line_variants}."
            )

        for variant in line.variants:
            self.visit(variant)

        self._lines.append(attr.evolve(line, variants=tuple(self._variants)))
        self._variants = []

    @visit.register(LineVariant)
    def _visit_line_variant(self, variant: LineVariant) -> None:
        alignment_manuscripts = self._alignment.get_number_of_manuscripts(
            self.line_index, self.variant_index
        )
        variant_manuscripts = len(variant.manuscripts)
        if alignment_manuscripts != variant_manuscripts:
            raise AlignmentError(
                "Invalid number of manuscripts. "
                f"Got {alignment_manuscripts}, expected {variant_manuscripts}."
            )

        for manuscript_line in variant.manuscripts:
            self.visit(manuscript_line)

        self._variants.append(
            attr.evolve(
                variant, manuscripts=tuple(self._manuscript_lines)
            ).set_alignment_flags()
        )
        self._manuscript_lines = []

    @visit.register(ManuscriptLine)
    def _visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        updated_line = manuscript_line.line.update_alignment(
            self.current_alignment.alignment
        )
        self._manuscript_lines.append(
            attr.evolve(
                manuscript_line,
                line=updated_line,
                omitted_words=self.current_alignment.omitted_words,
            )
        )

    def _validate_chapter(self, chapter: Chapter) -> None:
        alignment_lines = self._alignment.get_number_of_lines()
        chapter_lines = len(chapter.lines)
        if alignment_lines != chapter_lines:
            raise AlignmentError(
                f"Invalid number of lines. Got {alignment_lines}, expected {chapter_lines}."
            )

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, lines=tuple(self._lines))

    def _after_chapter_update(self) -> None:
        self._lines = []

from typing import List

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter, Line, LineVariant, ManuscriptLine
from ebl.transliteration.domain.alignment import AlignmentError
from ebl.corpus.domain.text import TextItem
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment


class AlignmentUpdater(ChapterUpdater):
    def __init__(self, chapter_index: int, alignment: Alignment):
        super().__init__(chapter_index)
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
            raise AlignmentError()

    @singledispatchmethod  # pyre-ignore[56]
    def visit(self, item: TextItem) -> None:
        super().visit(item)

    @visit.register(Chapter)  # pyre-ignore[56]
    def _visit_chapter(self, chapter: Chapter) -> None:
        if self._alignment.get_number_of_lines() == len(chapter.lines):
            super()._visit_chapter(chapter)
        else:
            raise AlignmentError()

    @visit.register(Line)  # pyre-ignore[56]
    def _visit_line(self, line: Line) -> None:
        if self._alignment.get_number_of_variants(self.variant_index) == len(
            line.variants
        ):
            for variant in line.variants:
                self.visit(variant)
            self._lines.append(attr.evolve(line, variants=tuple(self._variants)))
            self._variants = []
        else:
            raise AlignmentError()

    @visit.register(LineVariant)  # pyre-ignore[56]
    def _visit_line_variant(self, variant: LineVariant) -> None:
        if self._alignment.get_number_of_manuscripts(
            self.line_index, self.variant_index
        ) == len(variant.manuscripts):
            for manuscript_line in variant.manuscripts:
                self.visit(manuscript_line)

            self._variants.append(
                attr.evolve(variant, manuscripts=tuple(self._manuscript_lines))
            )
            self._manuscript_lines = []
        else:
            raise AlignmentError()

    @visit.register(ManuscriptLine)  # pyre-ignore[56]
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

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        if self._alignment.get_number_of_lines() == len(chapter.lines):
            return attr.evolve(chapter, lines=tuple(self._lines))
        else:
            raise AlignmentError()

    def _after_chapter_update(self) -> None:
        self._lines = []

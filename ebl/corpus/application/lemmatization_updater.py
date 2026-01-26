from functools import singledispatchmethod
from typing import List, Sequence

import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lemmatization import ChapterLemmatization
from ebl.corpus.domain.chapter import Chapter, ChapterItem
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.text_line import update_tokens


class LemmatizationUpdater(ChapterUpdater):
    def __init__(self, lemmatization: ChapterLemmatization):
        super().__init__()
        self._lemmatization = lemmatization
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
    def current_lemmatization(self) -> Sequence[LemmatizationToken]:
        try:
            return self._lemmatization[self.line_index][self.variant_index].manuscripts[
                self.manuscript_line_index
            ]
        except IndexError:
            raise LemmatizationError(
                f"No lemmatization for line {self.line_index} "
                f"variant {self.variant_index} "
                f"manuscript {self.manuscript_line_index}."
            )

    @singledispatchmethod
    def visit(self, item: ChapterItem) -> None:
        super().visit(item)

    @visit.register(Line)
    def _visit_line(self, line: Line) -> None:
        for variant in line.variants:
            self.visit(variant)

        if len(self._lemmatization[self.line_index]) == len(line.variants):
            self._lines.append(attr.evolve(line, variants=tuple(self._variants)))
            self._variants = []
        else:
            raise LemmatizationError()

    @visit.register(LineVariant)
    def _visit_line_variant(self, variant: LineVariant) -> None:
        for manuscript_line in variant.manuscripts:
            self.visit(manuscript_line)

        if len(
            self._lemmatization[self.line_index][self.variant_index].manuscripts
        ) == len(variant.manuscripts):
            self._variants.append(
                attr.evolve(
                    variant,
                    reconstruction=update_tokens(
                        variant.reconstruction,
                        self._lemmatization[self.line_index][
                            self.variant_index
                        ].reconstruction,
                        lambda token, lemmatization_token: token.set_unique_lemma(
                            lemmatization_token
                        ),
                        LemmatizationError,
                    ),
                    manuscripts=tuple(self._manuscript_lines),
                )
            )
            self._manuscript_lines = []
        else:
            raise LemmatizationError()

    @visit.register(ManuscriptLine)
    def _visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        updated_line = manuscript_line.line.update_lemmatization(
            self.current_lemmatization
        )
        self._manuscript_lines.append(attr.evolve(manuscript_line, line=updated_line))

    def _validate_chapter(self, chapter: Chapter) -> None:
        if len(self._lemmatization) != len(chapter.lines):
            raise LemmatizationError()

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return attr.evolve(chapter, lines=tuple(self._lines))

    def _after_chapter_update(self) -> None:
        self._lines = []

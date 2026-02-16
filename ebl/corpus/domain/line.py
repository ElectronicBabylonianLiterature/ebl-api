from typing import Optional, Sequence

import attr
import pydash
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine, ManuscriptLineLabel

from ebl.merger import Merger
from ebl.transliteration.domain.line_number import AbstractLineNumber, OldLineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import TranslationLine


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: AbstractLineNumber
    variants: Sequence[LineVariant]
    old_line_numbers: Sequence[OldLineNumber] = attr.ib(default=())
    is_second_line_of_parallelism: bool = False
    is_beginning_of_section: bool = False
    translation: Sequence[TranslationLine] = attr.ib(default=())

    @translation.validator
    def _validate_translations(self, _, value: Sequence[TranslationLine]) -> None:
        if any(line.extent and line.extent.labels for line in value):
            raise ValueError("Labels are not allowed in line translations.")

    @property
    def manuscript_ids(self) -> Sequence[int]:
        return [
            manuscript_id
            for variant in self.variants
            for manuscript_id in variant.manuscript_ids
        ]

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [
            label
            for variant in self.variants
            for label in variant.manuscript_line_labels
        ]

    def get_manuscript_line(self, manuscript_id: int) -> ManuscriptLine:
        manuscript_line = (
            pydash.chain(self.variants)
            .map_(lambda variant: variant.get_manuscript_line(manuscript_id))
            .reject(pydash.is_none)
            .head()
            .value()
        )
        if manuscript_line is None:
            raise ValueError(f"No line found for manuscript {manuscript_id}.")
        else:
            return manuscript_line

    def get_manuscript_text_lines(self, manuscript_id: int) -> Sequence[TextLine]:
        return [
            line
            for variant in self.variants
            for line in variant.get_manuscript_text_lines(manuscript_id)
        ]

    def get_manuscript_text_line(self, manuscript_id: int) -> Optional[TextLine]:
        return (
            pydash.chain(self.variants)
            .map_(lambda variant: variant.get_manuscript_text_line(manuscript_id))
            .reject(pydash.is_none)
            .head()
            .value()
        )

    def merge(self, other: "Line") -> "Line":
        def inner_merge(old: LineVariant, new: LineVariant) -> LineVariant:
            return old.merge(new)

        merged_variants = Merger(repr, inner_merge).merge(self.variants, other.variants)
        return attr.evolve(other, variants=tuple(merged_variants))

    def set_variant_alignment_flags(self) -> "Line":
        return attr.evolve(
            self,
            variants=tuple(variant.set_alignment_flags() for variant in self.variants),
        )

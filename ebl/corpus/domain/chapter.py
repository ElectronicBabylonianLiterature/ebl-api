from enum import Enum, unique
from typing import Optional, Sequence, Tuple, TypeVar, Union, cast

import attr
import pydash

from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.label_validator import LabelValidator
from ebl.corpus.domain.manuscript import Manuscript, Siglum
from ebl.corpus.domain.stage import Stage
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.merger import Merger
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.text_line import AlignmentMap, TextLine, merge_tokens
from ebl.transliteration.domain.tokens import Token
from ebl.corpus.domain.create_alignment_map import create_alignment_map


@unique
class Classification(Enum):
    ANCIENT = "Ancient"
    MODERN = "Modern"


T = TypeVar("T")


def validate_labels(_instance, _attribute, value: Sequence[Label]) -> None:
    validator = LabelValidator()
    for label in value:
        label.accept(validator)

    if not validator.is_valid:
        raise ValueError(f'Invalid labels "{[value.to_value() for value in value]}".')


ManuscriptLineLabel = Tuple[int, Sequence[Label], AbstractLineNumber]


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Sequence[Label] = attr.ib(validator=validate_labels)
    line: Union[TextLine, EmptyLine]
    paratext: Sequence[Union[DollarLine, NoteLine]] = tuple()
    omitted_words: Sequence[int] = tuple()

    @property
    def label(self) -> Optional[ManuscriptLineLabel]:
        return (
            (self.manuscript_id, self.labels, cast(TextLine, self.line).line_number)
            if isinstance(self.line, TextLine)
            else None
        )

    def merge(self, other: "ManuscriptLine") -> "ManuscriptLine":
        merged_line = self.line.merge(other.line)
        return attr.evolve(other, line=merged_line)

    def update_alignments(self, aligment_map: AlignmentMap) -> "ManuscriptLine":
        return attr.evolve(
            self,
            line=self.line.update_alignments(aligment_map),
            omitted_words=tuple(
                aligment_map[index]
                for index in self.omitted_words
                if index < len(aligment_map) and aligment_map[index] is not None
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class LineVariant:
    reconstruction: Sequence[Token] = attr.ib(
        converter=pydash.flow(set_enclosure_type, set_language)
    )
    note: Optional[NoteLine] = None
    manuscripts: Sequence[ManuscriptLine] = tuple()
    parallel_lines: Sequence[ParallelLine] = tuple()

    @reconstruction.validator
    def validate_reconstruction(self, _, value):
        validate(value)

    @property
    def manuscript_ids(self) -> Sequence[int]:
        return [manuscript.manuscript_id for manuscript in self.manuscripts]

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [
            cast(ManuscriptLineLabel, manuscript_line.label)
            for manuscript_line in self.manuscripts
            if manuscript_line.label
        ]

    def get_manuscript_text_line(self, manuscript_id: int) -> Optional[TextLine]:
        return (
            pydash.chain(self.manuscripts)
            .filter(lambda manuscript: manuscript.manuscript_id == manuscript_id)
            .map_(lambda manuscript: manuscript.line)
            .filter(lambda line: isinstance(line, TextLine))
            .head()
            .value()
        )

    def merge(self, other: "LineVariant") -> "LineVariant":
        merged_reconstruction = merge_tokens(self.reconstruction, other.reconstruction)
        alignment_map = create_alignment_map(self.reconstruction, merged_reconstruction)

        def merge_manuscript(
            old: ManuscriptLine, new: ManuscriptLine
        ) -> ManuscriptLine:
            return old.merge(new).update_alignments(alignment_map)

        merged_manuscripts = Merger(repr, merge_manuscript).merge(
            self.manuscripts, other.manuscripts
        )
        return attr.evolve(
            other,
            reconstruction=merged_reconstruction,
            manuscripts=tuple(merged_manuscripts),
        )


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: AbstractLineNumber
    variants: Sequence[LineVariant]
    is_second_line_of_parallelism: bool = False
    is_beginning_of_section: bool = False

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


@attr.s(auto_attribs=True, frozen=True)
class TextLineEntry:
    line: TextLine
    source: Optional[int] = None


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ""
    name: str = ""
    order: int = 0
    manuscripts: Sequence[Manuscript] = attr.ib(default=tuple())
    uncertain_fragments: Sequence[MuseumNumber] = tuple()
    lines: Sequence[Line] = attr.ib(default=tuple())
    signs: Sequence[str] = tuple()
    parser_version: str = ""

    @manuscripts.validator
    def _validate_manuscript_ids(self, _, value: Sequence[Manuscript]) -> None:
        duplicate_ids = pydash.duplicates([manuscript.id for manuscript in value])
        if duplicate_ids:
            raise ValueError(f"Duplicate manuscript IDs: {duplicate_ids}.")

    @manuscripts.validator
    def _validate_manuscript_sigla(self, _, value: Sequence[Manuscript]) -> None:
        duplicate_sigla = pydash.duplicates([manuscript.siglum for manuscript in value])
        if duplicate_sigla:
            raise ValueError(f"Duplicate sigla: {duplicate_sigla}.")

    @lines.validator
    def _validate_orphan_manuscript_ids(self, _, value: Sequence[Line]) -> None:
        manuscript_ids = {manuscript.id for manuscript in self.manuscripts}
        used_manuscripts_ids = {
            manuscript_id
            for line in self.lines
            for manuscript_id in line.manuscript_ids
        }
        orphans = used_manuscripts_ids - manuscript_ids
        if orphans:
            raise ValueError(f"Missing manuscripts: {orphans}.")

    @lines.validator
    def _validate_line_numbers(self, _, value: Sequence[Line]) -> None:
        duplicates = pydash.duplicates([line.number for line in value])
        if any(duplicates):
            raise ValueError(f"Duplicate line numbers: {duplicates}.")

    @lines.validator
    def _validate_manuscript_line_labels(self, _, value: Sequence[Line]) -> None:
        duplicates = pydash.duplicates(self._manuscript_line_labels)
        if duplicates:
            readable_labels = self._make_labels_readable(duplicates)
            raise ValueError(f"Duplicate manuscript line labels: {readable_labels}.")

    @property
    def text_lines(self) -> Sequence[Sequence[TextLineEntry]]:
        return [
            self._get_manuscript_text_lines(manuscript)
            for manuscript in self.manuscripts
        ]

    @property
    def invalid_lines(self) -> Sequence[Tuple[Siglum, TextLineEntry]]:
        text_lines = self.text_lines
        return [
            (self.manuscripts[index].siglum, text_lines[index][number])
            for index, signs in enumerate(self.signs)
            for number, line in enumerate(signs.split("\n"))
            if "?" in line
        ]

    @property
    def _manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [label for line in self.lines for label in line.manuscript_line_labels]

    def merge(self, other: "Chapter") -> "Chapter":
        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(repr, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(other, lines=tuple(merged_lines))

    def _get_manuscript_text_lines(
        self, manuscript: Manuscript
    ) -> Sequence[TextLineEntry]:
        def create_entry(line: Line, index: int) -> Optional[TextLineEntry]:
            text_line = line.get_manuscript_text_line(manuscript.id)
            return text_line and TextLineEntry(text_line, index)

        return (
            pydash.chain(self.lines)
            .map_(create_entry)
            .reject(pydash.is_none)
            .concat(
                [TextLineEntry(line, None) for line in manuscript.colophon_text_lines]
            )
            .value()
        )

    def _get_manuscript(self, id_: int) -> Manuscript:
        try:
            return next(
                manuscript for manuscript in self.manuscripts if manuscript.id == id_
            )
        except StopIteration:
            raise NotFoundError(f"No manuscripts with id {id_}.")

    def _make_labels_readable(self, labels: Sequence[ManuscriptLineLabel]) -> str:
        return ", ".join(
            " ".join(
                [
                    str(self._get_manuscript(label[0]).siglum),
                    *[side.to_value() for side in label[1]],
                    label[2].label,
                ]
            )
            for label in labels
        )

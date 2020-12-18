from enum import Enum, unique
from typing import Optional, Sequence, Set, Tuple, TypeVar, Union, cast

import attr
import pydash  # pyre-ignore[21]

from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.label_validator import LabelValidator
from ebl.corpus.domain.manuscript import Manuscript
from ebl.errors import NotFoundError
from ebl.merger import Merger
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token


@unique
class Classification(Enum):
    ANCIENT = "Ancient"
    MODERN = "Modern"


@unique
class Stage(Enum):
    UR_III = "Ur III"
    OLD_ASSYRIAN = "Old Assyrian"
    OLD_BABYLONIAN = "Old Babylonian"
    MIDDLE_BABYLONIAN = "Middle Babylonian"
    MIDDLE_ASSYRIAN = "Middle Assyrian"
    HITTITE = "Hittite"
    NEO_ASSYRIAN = "Neo-Assyrian"
    NEO_BABYLONIAN = "Neo-Babylonian"
    LATE_BABYLONIAN = "Late Babylonian"
    PERSIAN = "Persian"
    HELLENISTIC = "Hellenistic"
    PARTHIAN = "Parthian"
    UNCERTAIN = "Uncertain"
    STANDARD_BABYLONIAN = "Standard Babylonian"


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

    def strip_alignments(self) -> "ManuscriptLine":
        return attr.evolve(
            self, line=self.line.strip_alignments(), omitted_words=tuple()
        )


@attr.s(auto_attribs=True, frozen=True)
class LineVariant:
    text: TextLine = attr.ib()
    note: Optional[NoteLine] = None
    manuscripts: Sequence[ManuscriptLine] = tuple()

    @text.validator
    def validate_reconstruction(self, _, value):
        validate(value.content)

    @property
    def number(self) -> AbstractLineNumber:
        return self.text.line_number

    @property
    def reconstruction(self) -> Sequence[Token]:
        return self.text.content

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

    def merge(self, other: "LineVariant") -> "LineVariant":
        def inner_merge(old: ManuscriptLine, new: ManuscriptLine) -> ManuscriptLine:
            return old.merge(new)

        merged_manuscripts = Merger(repr, inner_merge).merge(
            self.manuscripts, other.manuscripts
        )
        merged = attr.evolve(other, manuscripts=tuple(merged_manuscripts))

        return (
            merged.strip_alignments()
            if self.reconstruction != other.reconstruction
            else merged
        )

    def strip_alignments(self) -> "LineVariant":
        stripped_manuscripts = tuple(
            manuscript_line.strip_alignments() for manuscript_line in self.manuscripts
        )
        return attr.evolve(self, manuscripts=stripped_manuscripts)


@attr.s(auto_attribs=True, frozen=True)
class Line:
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

    @property
    def line_numbers(self) -> Set[AbstractLineNumber]:
        return {variant.text.line_number for variant in self.variants}

    def merge(self, other: "Line") -> "Line":
        def inner_merge(old: LineVariant, new: LineVariant) -> LineVariant:
            return old.merge(new)

        merged_variants = Merger(repr, inner_merge).merge(self.variants, other.variants)
        return attr.evolve(other, variants=tuple(merged_variants))


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ""
    name: str = ""
    order: int = 0
    manuscripts: Sequence[Manuscript] = attr.ib(default=tuple())
    lines: Sequence[Line] = attr.ib(default=tuple())
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
        duplicates = pydash.duplicates(
            [line_number for line in value for line_number in line.line_numbers]
        )
        if any(duplicates):
            raise ValueError(f"Duplicate line numbers: {duplicates}.")

    @lines.validator
    def _validate_manuscript_line_labels(self, _, value: Sequence[Line]) -> None:
        duplicates = pydash.duplicates(self._manuscript_line_labels)
        if duplicates:
            readable_labels = self._make_labels_readable(duplicates)
            raise ValueError(f"Duplicate manuscript line labels: {readable_labels}.")

    @property
    def _manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [label for line in self.lines for label in line.manuscript_line_labels]

    def merge(self, other: "Chapter") -> "Chapter":
        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(repr, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(other, lines=tuple(merged_lines))

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

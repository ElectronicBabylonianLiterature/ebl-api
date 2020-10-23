import collections
from typing import Iterable, Optional, Sequence, Set, TypeVar, Union

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.enums import (
    Classification,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Stage,
)
from ebl.corpus.domain.label_validator import LabelValidator
import ebl.corpus.domain.text_visitor as text_visitor
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.tokens import Token
from ebl.merger import Merger
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.line import EmptyLine


TextId = collections.namedtuple("TextId", ["category", "index"])


T = TypeVar("T")


def get_duplicates(collection: Iterable[T]) -> Set[T]:
    return {
        item for item, count in collections.Counter(collection).items() if count > 1
    }


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    id: int
    siglum_disambiguator: str = ""
    museum_number: Optional[MuseumNumber] = None
    accession: str = attr.ib(default="")
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = Provenance.NINEVEH
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ""
    references: Sequence[Reference] = tuple()

    @accession.validator
    def validate_accession(self, _, value):
        if self.museum_number and value:
            raise ValueError("Accession given when museum number present.")

    @property
    def siglum(self):
        return (self.provenance, self.period, self.type, self.siglum_disambiguator)

    def accept(self, visitor: text_visitor.TextVisitor) -> None:
        visitor.visit_manuscript(self)


def validate_labels(_instance, _attribute, value: Sequence[Label]) -> None:
    validator = LabelValidator()
    for label in value:
        label.accept(validator)

    if not validator.is_valid:
        raise ValueError(f'Invalid labels "{[value.to_value() for value in value]}".')


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Sequence[Label] = attr.ib(validator=validate_labels)
    line: Union[TextLine, EmptyLine]
    paratext: Sequence[Union[DollarLine, NoteLine]] = tuple()

    def accept(self, visitor: text_visitor.TextVisitor) -> None:
        visitor.visit_manuscript_line(self)

    def merge(self, other: "ManuscriptLine") -> "ManuscriptLine":
        merged_line = self.line.merge(other.line)
        return attr.evolve(other, line=merged_line)

    def strip_alignments(self) -> "ManuscriptLine":
        return attr.evolve(self, line=self.line.strip_alignments())


@attr.s(auto_attribs=True, frozen=True)
class Line:
    text: TextLine = attr.ib()
    note: Optional[NoteLine] = None
    is_second_line_of_parallelism: bool = False
    is_beginning_of_section: bool = False
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
    def manuscript_ids(self) -> Set[int]:
        return {manuscript.manuscript_id for manuscript in self.manuscripts}

    def accept(self, visitor: text_visitor.TextVisitor) -> None:
        if visitor.is_pre_order:
            visitor.visit_line(self)

        for manuscript_line in self.manuscripts:
            manuscript_line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_line(self)

    def merge(self, other: "Line") -> "Line":
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

    def strip_alignments(self) -> "Line":
        stripped_manuscripts = tuple(
            manuscript_line.strip_alignments() for manuscript_line in self.manuscripts
        )
        return attr.evolve(self, manuscripts=stripped_manuscripts)


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
        duplicate_ids = get_duplicates(manuscript.id for manuscript in value)
        if duplicate_ids:
            raise ValueError(f"Duplicate manuscript IDs: {duplicate_ids}.")

    @manuscripts.validator
    def _validate_manuscript_sigla(self, _, value: Sequence[Manuscript]) -> None:
        duplicate_sigla = get_duplicates(manuscript.siglum for manuscript in value)
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
        counter = collections.Counter(line.text.line_number for line in value)
        duplicates = [number.label for number in counter if counter[number] > 1]
        if any(duplicates):
            raise ValueError(f"Duplicate line numbers: {duplicates}.")

    def accept(self, visitor: text_visitor.TextVisitor) -> None:
        if visitor.is_pre_order:
            visitor.visit_chapter(self)

        for manuscript in self.manuscripts:
            manuscript.accept(visitor)

        for line in self.lines:
            line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_chapter(self)

    def merge(self, other: "Chapter") -> "Chapter":
        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(repr, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(other, lines=tuple(merged_lines))


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    chapters: Sequence[Chapter] = tuple()

    @property
    def id(self) -> TextId:

        return TextId(self.category, self.index)

    def accept(self, visitor: text_visitor.TextVisitor) -> None:
        if visitor.is_pre_order:
            visitor.visit_text(self)

        for chapter in self.chapters:
            chapter.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_text(self)

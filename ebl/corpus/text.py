import collections
from enum import Enum, auto
from typing import Tuple

import attr

from ebl.bibliography.reference import Reference
from ebl.corpus.enums import Classification, ManuscriptType, Period, \
    PeriodModifier, Provenance, Stage
from ebl.corpus.label_validator import LabelValidator
from ebl.merger import Merger
from ebl.reconstruction.enclosure_validator import validate
from ebl.reconstruction.reconstructed_text import ReconstructionToken, \
    ReconstructionTokenVisitor
from ebl.transliteration.labels import Label, LineNumberLabel
from ebl.transliteration.line import TextLine

TextId = collections.namedtuple('TextId', ['category', 'index'])


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    id: int
    siglum_disambiguator: str = ''
    museum_number: str = ''
    accession: str = attr.ib(default='')
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = Provenance.NINEVEH
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ''
    references: Tuple[Reference, ...] = tuple()

    @accession.validator
    def validate_accession(self, _, value):
        if self.museum_number and value:
            raise ValueError(f'Accession given when museum number present.')

    @property
    def siglum(self):
        return (self.provenance,
                self.period,
                self.type,
                self.siglum_disambiguator)

    def accept(self, visitor: 'TextVisitor') -> None:
        visitor.visit_manuscript(self)


def validate_labels(_instance, _attribute, value: Tuple[Label, ...]) -> None:
    validator = LabelValidator()
    for label in value:
        label.accept(validator)

    if not validator.is_valid:
        raise ValueError(
            f'Invalid labels "{[value.to_value() for value in value]}".'
        )


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Tuple[Label, ...] = attr.ib(validator=validate_labels)
    line: TextLine

    def accept(self, visitor: 'TextVisitor') -> None:
        visitor.visit_manuscript_line(self)

    def merge(self, other: 'ManuscriptLine') -> 'ManuscriptLine':
        merged_line = self.line.merge(other.line)
        return attr.evolve(other, line=merged_line)

    def strip_alignments(self) -> 'ManuscriptLine':
        return attr.evolve(self, line=self.line.strip_alignments())


def map_manuscript_line(manuscript_line: ManuscriptLine) -> str:
    labels = ' '.join(label.to_atf() for label in manuscript_line.labels)
    manuscript_id = manuscript_line.manuscript_id
    return f'{manuscript_id}⋮{labels}⋮{manuscript_line.line.atf}'


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: LineNumberLabel
    reconstruction: Tuple[ReconstructionToken, ...] = \
        attr.ib(default=tuple())
    manuscripts: Tuple[ManuscriptLine, ...] = tuple()

    @reconstruction.validator
    def validate_reconstruction(self, _, value):

        validate(value)

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_line(self)

        for token in self.reconstruction:
            token.accept(visitor)

        for manuscript_line in self.manuscripts:
            manuscript_line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_line(self)

    def merge(self, other: 'Line') -> 'Line':
        def inner_merge(old: ManuscriptLine,
                        new: ManuscriptLine) -> ManuscriptLine:
            return old.merge(new)

        merged_manuscripts = Merger(
            map_manuscript_line,
            inner_merge
        ).merge(
            self.manuscripts, other.manuscripts
        )
        merged = attr.evolve(other, manuscripts=tuple(merged_manuscripts))

        return (merged.strip_alignments()
                if self.reconstruction != other.reconstruction
                else merged)

    def strip_alignments(self) -> 'Line':
        stripped_manuscripts = tuple(
            manuscript_line.strip_alignments()
            for manuscript_line in self.manuscripts
        )
        return attr.evolve(self, manuscripts=stripped_manuscripts)


def map_line(line: Line) -> str:
    number = line.number.to_atf()
    reconstruction = ' '.join(str(token) for token in line.reconstruction)
    lines = '⋮⋮'.join(
        map_manuscript_line(manuscript_line) for manuscript_line in
        line.manuscripts)
    return f'{number}⋮⋮{reconstruction}⋮⋮{lines}'


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ''
    name: str = ''
    order: int = 0
    manuscripts: Tuple[Manuscript, ...] = tuple()
    lines: Tuple[Line, ...] = tuple()

    def __attrs_post_init__(self) -> None:
        self.accept(ManuscriptIdValidator())

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_chapter(self)

        for manuscript in self.manuscripts:
            manuscript.accept(visitor)

        for line in self.lines:
            line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_chapter(self)

    def merge(self, other: 'Chapter') -> 'Chapter':
        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(
            map_line,
            inner_merge
        ).merge(
            self.lines, other.lines
        )
        return attr.evolve(other, lines=tuple(merged_lines))


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    chapters: Tuple[Chapter, ...] = tuple()

    @property
    def id(self) -> TextId:

        return TextId(self.category, self.index)

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_text(self)

        for chapter in self.chapters:
            chapter.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_text(self)


class TextVisitor(ReconstructionTokenVisitor):
    class Order(Enum):
        PRE = auto()
        POST = auto()

    def __init__(self, order: 'TextVisitor.Order'):
        self._order = order

    @property
    def is_post_order(self) -> bool:
        return self._order == TextVisitor.Order.POST

    @property
    def is_pre_order(self) -> bool:
        return self._order == TextVisitor.Order.PRE

    def visit_text(self, text: Text) -> None:
        pass

    def visit_chapter(self, chapter: Chapter) -> None:
        pass

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        pass

    def visit_line(self, line: Line) -> None:
        pass

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        pass


class ManuscriptIdValidator(TextVisitor):

    def __init__(self):
        super().__init__(TextVisitor.Order.POST)
        self._manuscripts_ids = []
        self._sigla = []
        self._used_manuscripts_ids = set()

    def visit_chapter(self, _) -> None:
        def get_duplicates(collection: list) -> list:
            return [item
                    for item, count
                    in collections.Counter(collection).items()
                    if count > 1]

        errors = []

        orphans = self._used_manuscripts_ids - set(self._manuscripts_ids)
        if orphans:
            errors.append(f'Missing manuscripts: {orphans}.')

        duplicate_ids = get_duplicates(self._manuscripts_ids)
        if duplicate_ids:
            errors.append(f'Duplicate manuscript IDs: {duplicate_ids}.')

        duplicate_sigla = get_duplicates(self._sigla)
        if duplicate_sigla:
            errors.append(f'Duplicate sigla: {duplicate_sigla}.')

        if errors:
            raise ValueError(f'Invalid manuscripts: {errors}.')

        self._manuscripts_ids = []
        self._sigla = []
        self._used_manuscripts_ids = set()

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        self._manuscripts_ids.append(manuscript.id)
        self._sigla.append(manuscript.siglum)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        self._used_manuscripts_ids.add(manuscript_line.manuscript_id)

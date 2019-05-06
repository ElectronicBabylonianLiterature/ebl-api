import collections
from enum import Enum, auto
from typing import Tuple

import attr
import pydash

from ebl.bibliography.reference import Reference
from ebl.text.labels import Label, LabelVisitor, SurfaceLabel, ColumnLabel, \
    LineNumberLabel
from ebl.text.line import TextLine
from ebl.text.text import create_tokens


class Classification(Enum):
    ANCIENT = 'Ancient'
    MODERN = 'Modern'


class SiglumEnum(Enum):
    def __init__(self, long_name, abbreviation):
        self.long_name = long_name
        self.abbreviation = abbreviation

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return [
            enum for enum in cls
            if enum.abbreviation == abbreviation
        ][0]

    @classmethod
    def from_name(cls, name):
        return [
            enum for enum in cls
            if enum.long_name == name
        ][0]


class ManuscriptType(Enum):
    LIBRARY = ('Library', '')
    SCHOOL = ('School', 'Sch')
    VARIA = ('Varia', 'Var')
    COMMENTARY = ('Commentary', 'Com')
    QUOTATION = ('Quotation', 'Quo')

    def __init__(self, long_name, abbreviation):
        self.long_name = long_name
        self.abbreviation = abbreviation

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return [
            enum for enum in cls
            if enum.abbreviation == abbreviation
        ][0]

    @classmethod
    def from_name(cls, name):
        return [
            enum for enum in cls
            if enum.long_name == name
        ][0]


class Provenance(Enum):
    ASSYRIA = ('Assyria', 'Assa', None)
    ASSUR = ('Aššur', 'Ašš', 'Assyria')
    HUZIRINA = ('Ḫuzirina', 'Huz', 'Assyria')
    KALHU = ('Kalḫu', 'Kal', 'Assyria')
    KHORSABAD = ('Khorsabad', 'Kho', 'Assyria')
    NINEVEH = ('Nineveh', 'Nin', 'Assyria')
    TARBISU = ('Tarbiṣu', 'Tar', 'Assyria')
    BABYLONIA = ('Babylonia', 'Baba', None)
    BABYLON = ('Babylon', 'Bab', 'Babylonia')
    BORSIPPA = ('Borsippa', 'Bor', 'Babylonia')
    CUTHA = ('Cutha', 'Cut', 'Babylonia')
    ISIN = ('Isin', 'Isn', 'Babylonia')
    KIS = ('Kiš', 'Kiš', 'Babylonia')
    LARSA = ('Larsa', 'Lar', 'Babylonia')
    METURAN = ('Meturan', 'Met', 'Babylonia')
    NEREBUN = ('Nērebtum', 'Nēr', 'Babylonia')
    NIPPUR = ('Nippur', 'Nip', 'Babylonia')
    SIPPAR = ('Sippar', 'Sip', 'Babylonia')
    SADUPPUM = ('Šaduppûm', 'Šad', 'Babylonia')
    UR = ('Ur', 'Ur', 'Babylonia')
    URUK = ('Uruk', 'Urk', 'Babylonia')
    PERIPHERY = ('Periphery', '', None)
    ALALAKS = ('Alalakh', 'Ala', 'Periphery')
    TELL_EL_AMARNA = ('Tell el-Amarna', 'Ama', 'Periphery')
    EMAR = ('Emar', 'Emr', 'Periphery')
    HATTUSA = ('Ḫattuša', 'Hat', 'Periphery')
    MARI = ('Mari', 'Mar', 'Periphery')
    MEGIDDO = ('Megiddo', 'Meg', 'Periphery')
    SUSA = ('Susa', 'Sus', 'Periphery')
    UGARIT = ('Ugarit', 'Uga', 'Periphery')
    UNCERTAIN = ('Uncertain', 'Unc', None)

    def __init__(self, long_name, abbreviation, parent):
        self.long_name = long_name
        self.abbreviation = abbreviation
        self.parent = parent

    @classmethod
    def from_name(cls, name):
        return [
            enum for enum in cls
            if enum.long_name == name
        ][0]


class PeriodModifier(Enum):
    NONE = 'None'
    EARLY = 'Early'
    LATE = 'Late'


class Period(Enum):
    UR_III = ('Ur III', 'Ur3', None)
    OLD_ASSYRIAN = ('Old Assyrian', 'OA', None)
    OLD_BABYLONIAN = ('Old Babylonian', 'OB', None)
    MIDDLE_BABYLONIAN = ('Middle Babylonian', 'MB', None)
    MIDDLE_ASSYRIAN = ('Middle Assyrian', 'MA', None)
    HITTITE = ('Hittite', 'Hit', None)
    NEO_ASSYRIAN = ('Neo-Assyrian', 'NA', None)
    NEO_BABYLONIAN = ('Neo-Babylonian', 'NB', None)
    LATE_BABYLONIAN = ('Late Babylonian', 'LB', None)
    PERSIAN = ('Persian', 'Per', 'Late Babylonian')
    HELLENISTIC = ('Hellenistic', 'Hel', 'Late Babylonian')
    PARTHIAN = ('Parthian', 'Par', 'Late Babylonian')
    UNCERTAIN = ('Uncertain', 'Unc', None)

    def __init__(self, long_name, abbreviation, parent):
        self.long_name = long_name
        self.abbreviation = abbreviation
        self.parent = parent

    @classmethod
    def from_name(cls, name):
        return [
            enum for enum in cls
            if enum.long_name == name
        ][0]


class Stage(Enum):
    UR_III = 'Ur III'
    OLD_ASSYRIAN = 'Old Assyrian'
    OLD_BABYLONIAN = 'Old Babylonian'
    MIDDLE_BABYLONIAN = 'Middle Babylonian'
    MIDDLE_ASSYRIAN = 'Middle Assyrian'
    HITTITE = 'Hittite'
    NEO_ASSYRIAN = 'Neo-Assyrian'
    NEO_BABYLONIAN = 'Neo-Babylonian'
    LATE_BABYLONIAN = 'Late Babylonian'
    PERSIAN = 'Persian'
    HELLENISTIC = 'Hellenistic'
    PARTHIAN = 'Parthian'
    UNCERTAIN = 'Uncertain'
    STANDARD_BABYLONIAN = 'Standard Babylonian'


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

    @staticmethod
    def from_dict(manuscript: dict) -> 'Manuscript':
        return Manuscript(
            manuscript['id'],
            manuscript['siglumDisambiguator'],
            manuscript['museumNumber'],
            manuscript['accession'],
            PeriodModifier(manuscript['periodModifier']),
            Period.from_name(manuscript['period']),
            Provenance.from_name(manuscript['provenance']),
            ManuscriptType.from_name(manuscript['type']),
            manuscript['notes'],
            tuple(
                Reference.from_dict(reference)
                for reference in manuscript['references']
            )
        )


class LabelValidator(LabelVisitor):
    def __init__(self):
        self.has_surface = False
        self.has_column = False
        self.is_valid = True

    def visit_surface_label(self, label: SurfaceLabel) -> 'LabelValidator':
        if self.has_surface or self.has_column:
            self.is_valid = False
        self.has_surface = True
        return self

    def visit_column_label(self, label: ColumnLabel) -> 'LabelValidator':
        if self.has_column:
            self.is_valid = False
        self.has_column = True
        return self

    def visit_line_number_label(self,
                                label: LineNumberLabel) -> 'LabelValidator':
        self.is_valid = False
        return self


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

    @staticmethod
    def from_dict(data):
        return ManuscriptLine(
            data['manuscriptId'],
            tuple(Label.parse(label) for label in data['labels']),
            TextLine.of_iterable(
                LineNumberLabel.from_atf(data['line']['prefix']),
                create_tokens(data['line']['content'])
            )
        )


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: LineNumberLabel
    reconstruction: str = ''
    manuscripts: Tuple[ManuscriptLine, ...] = tuple()

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_line(self)

        for manuscript_line in self.manuscripts:
            manuscript_line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_line(self)

    @staticmethod
    def from_dict(data):
        return Line(LineNumberLabel(data['number']),
                    data['reconstruction'],
                    tuple(ManuscriptLine.from_dict(line)
                          for line in data['manuscripts']))


def validate_manuscripts(_instance, _attribute, value):
    def not_unique(entry_mapper):
        return (
            pydash
            .chain(value)
            .map_(entry_mapper)
            .map_(lambda entry, _, entries: (entry, entries.count(entry)))
            .filter(lambda entry: entry[1] > 1)
            .map_(lambda entry: entry[0])
            .uniq()
            .value()
        )

    errors = []

    duplicate_ids = not_unique(lambda manuscript: manuscript.id)
    if duplicate_ids:
        errors.append(f'Duplicate manuscript IDs: {duplicate_ids}.')

    duplicate_sigla = not_unique(lambda manuscript: manuscript.siglum)
    if duplicate_sigla:
        errors.append(f'Duplicate sigla: {duplicate_sigla}.')

    if errors:
        raise ValueError(f'Invalid manuscripts: {errors}.')


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ''
    name: str = ''
    order: int = 0
    manuscripts: Tuple[Manuscript, ...] = attr.ib(
        default=attr.Factory(tuple),
        validator=validate_manuscripts
    )
    lines: Tuple[Line, ...] = tuple()

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_chapter(self)

        for manuscript in self.manuscripts:  # pylint: disable=E1133
            manuscript.accept(visitor)

        for line in self.lines:
            line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_chapter(self)

    @staticmethod
    def from_dict(chapter: dict) -> 'Chapter':
        return Chapter(
            Classification(chapter['classification']),
            Stage(chapter['stage']),
            chapter['version'],
            chapter['name'],
            chapter['order'],
            tuple(
                Manuscript.from_dict(manuscript)
                for manuscript in chapter['manuscripts']
            ),
            tuple(
                Line.from_dict(line)
                for line in chapter.get('lines', [])
            )
        )


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
        # pylint: disable=C0103
        return TextId(self.category, self.index)

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_text(self)

        for chapter in self.chapters:
            chapter.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_text(self)

    @staticmethod
    def from_dict(text: dict) -> 'Text':
        return Text(
            text['category'],
            text['index'],
            text['name'],
            text['numberOfVerses'],
            text['approximateVerses'],
            tuple(
                Chapter.from_dict(chapter)
                for chapter in text['chapters']
            )
        )


class TextVisitor:

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

import collections
import re
from enum import Enum
from typing import Dict, List, Tuple, Union

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


ManuscriptDict = Dict[str, Union[int, str, List[dict]]]


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

    def to_dict(self, include_documents=False) -> ManuscriptDict:
        # pylint: disable=E1101
        return {
            'id': self.id,
            'siglumDisambiguator': self.siglum_disambiguator,
            'museumNumber': self.museum_number,
            'accession': self.accession,
            'periodModifier': self.period_modifier.value,
            'period': self.period.long_name,
            'provenance': self.provenance.long_name,
            'type': self.type.long_name,
            'notes': self.notes,
            'references': [
                reference.to_dict(include_documents)
                for reference in self.references
            ]
        }

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


ManuscriptLineDict = Dict[str, Union[int, List[str], dict]]


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

    def to_dict(self) -> ManuscriptLineDict:
        # pylint: disable=E1133
        return {
            'manuscriptId': self.manuscript_id,
            'labels': [label.to_value() for label in self.labels],
            'line': self.line.to_dict()
        }

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


LineDict = Dict[str, Union[str, List[ManuscriptLineDict]]]


def validate_line_number(_instance, _attribute, value):
    if not re.fullmatch(r'[^\s]+', value):
        raise ValueError(f'Line number "{value}" is not a sequence of '
                         'non-space characters.')


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: str = attr.ib(validator=validate_line_number)
    reconstruction: str = ''
    manuscripts: Tuple[ManuscriptLine, ...] = tuple()

    def to_dict(self) -> LineDict:
        return {
            'number': self.number,
            'reconstruction': self.reconstruction,
            'manuscripts': [line.to_dict() for line in self.manuscripts]
        }

    @staticmethod
    def from_dict(data):
        return Line(data['number'], data['reconstruction'], tuple(
            ManuscriptLine.from_dict(line) for line in data['manuscripts']
        ))


ChapterDict = Dict[str, Union[
    int, str, List[ManuscriptDict], List[LineDict]
]]


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

    def to_dict(self, include_documents=False) -> ChapterDict:
        return {
            'classification': self.classification.value,
            'stage': self.stage.value,
            'version': self.version,
            'name': self.name,
            'order': self.order,
            'manuscripts': [
                manuscript.to_dict(include_documents)
                for manuscript in self.manuscripts  # pylint: disable=E1133
            ],
            'lines': [line.to_dict() for line in self.lines]
        }

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


TextDict = Dict[str, Union[int, str, List[ChapterDict]]]


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

    def to_dict(self, include_documents=False) -> TextDict:
        return {
            'category': self.category,
            'index': self.index,
            'name': self.name,
            'numberOfVerses': self.number_of_verses,
            'approximateVerses': self.approximate_verses,
            'chapters': [
                chapter.to_dict(include_documents)
                for chapter in self.chapters
            ]
        }

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

import collections
from enum import Enum
from typing import Dict, List, Tuple, Union

import attr
import pydash

from ebl.bibliography.reference import Reference


class Classification(Enum):
    ANCIENT = 'Ancient'
    MODERN = 'Modern'


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
    ASSYRIA = ('Assyria', None)
    ASSUR = ('Aššur', 'Assyria')
    HUZIRINA = ('Ḫuzirina', 'Assyria')
    KALHU = ('Kalḫu', 'Assyria')
    KHORSABAD = ('Khorsabad', 'Assyria')
    NINEVEH = ('Nineveh', 'Assyria')
    TARBISU = ('Tarbiṣu', 'Assyria')
    BABYLONIA = ('Babylonia', None)
    BABYLON = ('Babylon', 'Babylonia')
    BORSIPPA = ('Borsippa', 'Babylonia')
    CUTHA = ('Cutha', 'Babylonia')
    ISIN = ('Isin', 'Babylonia')
    KIS = ('Kiš', 'Babylonia')
    LARSA = ('Larsa', 'Babylonia')
    METURAN = ('Meturan', 'Babylonia')
    NEREBUN = ('Nērebtum', 'Babylonia')
    NIPPUR = ('Nippur', 'Babylonia')
    SIPPAR = ('Sippar', 'Babylonia')
    SADUPPUM = ('Šaduppûm', 'Babylonia')
    UR = ('Ur', 'Babylonia')
    URUK = ('Uruk', 'Babylonia')
    PERIPHERY = ('Periphery', None)
    ALALAKS = ('Alalakh', 'Periphery')
    TELL_EL_AMARNA = ('Tell el-Amarna', 'Periphery')
    EMAR = ('Emar', 'Periphery')
    HATTUSA = ('Ḫattuša', 'Periphery')
    MARI = ('Mari', 'Periphery')
    MEGIDDO = ('Megiddo', 'Periphery')
    SUSA = ('Susa', 'Periphery')
    UGARIT = ('Ugarit', 'Periphery')
    UNCERTAIN = ('Uncertain', None)

    def __init__(self, long_name, parent):
        self.long_name = long_name
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
            'period': self.period.value,
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
            Period(manuscript['period']),
            Provenance.from_name(manuscript['provenance']),
            ManuscriptType.from_name(manuscript['type']),
            manuscript['notes'],
            tuple(
                Reference.from_dict(reference)
                for reference in manuscript['references']
            )
        )


LineDict = Dict[str, Union[str, List[dict]]]


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: str
    reconstruction: str = ''
    manuscripts: tuple = tuple()

    def to_dict(self) -> LineDict:
        return {
            'number': self.number,
            'reconstruction': self.reconstruction,
            'manuscripts': []
        }

    @staticmethod
    def from_dict(data):
        return Line(data['number'], data['reconstruction'])


ChapterDict = Dict[str, Union[
    int, str, List[ManuscriptDict], List[LineDict]
]]


def validate_manuscripts(instance_, attribute_, value):
    # pylint: disable=W0613
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

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
    ASSUR = ('Aššur', 'Ašš')
    BABYLON = ('Babylon', 'Bab')
    BABYLONIA = ('Babylonia', 'Baba')
    BORSIPPA = ('Borsippa', 'Bor')
    HUZIRINA = ('Ḫuzirina', 'Bor')
    KALHU = ('Kalḫu', 'Kal')
    NINEVEH = ('Nineveh', 'Nin')
    NIPPUR = ('Nippur', 'Nin')
    SIPPAR = ('Sippar', 'Sip')
    SADUPPUM = ('Šaduppûm', 'Šad')
    UR = ('Ur', 'Ur')
    URUK = ('Uruk', 'Uru')
    UNCERTAIN = ('Uncertain', 'Unc')

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


class PeriodModifier(Enum):
    NONE = 'None'
    EARLY = 'Early'
    LATE = 'Late'


PERIOD_NAMES = {
    'UR_III': 'Ur III',
    'OLD_ASSYRIAN': 'Old Assyrian',
    'OLD_BABYLONIAN': 'Old Babylonian',
    'MIDDLE_BABYLONIAN': 'Middle Babylonian',
    'MIDDLE_ASSYRIAN': 'Middle Assyrian',
    'HITTITE': 'Hittite',
    'NEO_ASSYRIAN': 'Neo-Assyrian',
    'NEO_BABYLONIAN': 'Neo-Babylonian',
    'LATE_BABYLONIAN': 'Late Babylonian',
    'PERSIAN': 'Persian',
    'HELLENISTIC': 'Hellenistic',
    'PARTHIAN': 'Parthian',
    'UNCERTAIN': 'Uncertain'
}


Period = Enum('Period', PERIOD_NAMES)


Stage = Enum('Stage', {
    **PERIOD_NAMES,
    'STANDARD_BABYLONIAN': 'Standard Babylonian'
})


ManuscriptDict = Dict[str, Union[int, str, List[dict]]]


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
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
        return {
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


ChapterDict = Dict[str, Union[int, str, List[ManuscriptDict]]]


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ''
    name: str = ''
    order: int = 0
    manuscripts: Tuple[Manuscript, ...] = attr.ib(
        default=attr.Factory(tuple)
    )

    @manuscripts.validator
    def validate_manuscripts(self, _, value):
        errors = []

        duplicate_sigla = (
            pydash
            .chain(value)
            .map_(lambda manuscript: manuscript.siglum)
            .map_(lambda siglum, _, sigla: (siglum, sigla.count(siglum)))
            .filter(lambda entry: entry[1] > 1)
            .map_(lambda entry: entry[0])
            .uniq()
            .value()
        )
        if duplicate_sigla:
            errors.append(f'Duplicate sigla: {duplicate_sigla}.')

        if errors:
            raise ValueError(f'Invalid manuscripts: {errors}.')

    def to_dict(self, include_documents=False) -> ChapterDict:
        return {
            'classification': self.classification.value,
            'stage': self.stage.value,
            'version': self.version,
            'name': self.name,
            'order': self.order,
            'manuscripts': [
                manuscript.to_dict(include_documents)
                for manuscript in self.manuscripts
            ]
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

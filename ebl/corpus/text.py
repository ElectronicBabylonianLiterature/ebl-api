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


class Period(Enum):
    UR_III = ('Ur III', 'UrIII')
    OLD_ASSYRIAN = ('Old Assyrian', 'OA')
    OLD_BABYLONIAN = ('Old Babylonian', 'OB')
    MIDDLE_BABYLONIAN = ('Middle Babylonian', 'MB')
    MIDDLE_ASSYRIAN = ('Middle Assyrian', 'MA')
    HITTITE = ('Hittite', 'Hit')
    NEO_ASSYRIAN = ('Neo-Assyrian', 'NA')
    NEO_BABYLONIAN = ('Neo-Babylonian', 'NB')
    ACHAEMENID = ('Achaemenid', 'Ach')
    HELLENISTIC = ('Hellenistic', 'Hel')
    PARTHIAN = ('Parthian', 'Par')
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


class Stage(Enum):
    UR_III = ('Ur III', 'UrIII')
    OLD_ASSYRIAN = ('Old Assyrian', 'OA')
    OLD_BABYLONIAN = ('Old Babylonian', 'OB')
    MIDDLE_BABYLONIAN = ('Middle Babylonian', 'MB')
    MIDDLE_ASSYRIAN = ('Middle Assyrian', 'MA')
    HITTITE = ('Hittite', 'Hit')
    NEO_ASSYRIAN = ('Neo-Assyrian', 'NA')
    NEO_BABYLONIAN = ('Neo-Babylonian', 'NB')
    ACHAEMENID = ('Achaemenid', 'Ach')
    HELLENISTIC = ('Hellenistic', 'Hel')
    PARTHIAN = ('Parthian', 'Par')
    UNCERTAIN = ('Uncertain', 'Unc')
    STANDARD_BABYLONIAN = ('Standard Babylonian', 'SB')

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


ManuscriptDict = Dict[str, Union[int, str, List[dict]]]


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    siglum_number: int
    museum_number: str
    accession: str = attr.ib()
    period: Period
    provenance: Provenance
    type: ManuscriptType
    references: Tuple[Reference, ...] = tuple()

    @accession.validator
    def validate_accession(self, _, value):
        if self.museum_number and value:
            raise ValueError(f'Accession given when museum number present.')

    @property
    def siglum(self):
        return (f'{self.provenance.abbreviation}'
                f'{self.period.abbreviation}'
                f'{self.type.abbreviation}'
                f'{self.siglum_number}')

    def to_dict(self, include_documents=False) -> ManuscriptDict:
        return {
            'siglumNumber': self.siglum_number,
            'museumNumber': self.museum_number,
            'accession': self.accession,
            'period': self.period.long_name,
            'provenance': self.provenance.long_name,
            'type': self.type.long_name,
            'references': [
                reference.to_dict(include_documents)
                for reference in self.references
            ]
        }

    @staticmethod
    def from_dict(manuscript: dict) -> 'Manuscript':
        return Manuscript(
            manuscript['siglumNumber'],
            manuscript['museumNumber'],
            manuscript['accession'],
            Period.from_name(manuscript['period']),
            Provenance.from_name(manuscript['provenance']),
            ManuscriptType.from_name(manuscript['type']),
            tuple(
                Reference.from_dict(reference)
                for reference in manuscript['references']
            )
        )


ChapterDict = Dict[str, Union[int, str, List[ManuscriptDict]]]


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification
    stage: Stage
    name: str
    order: int
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
            'stage': self.stage.long_name,
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
            Stage.from_name(chapter['stage']),
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

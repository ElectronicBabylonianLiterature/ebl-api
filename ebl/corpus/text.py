from enum import Enum
from typing import Dict, List, Tuple, Union
import attr


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


ManuscriptDict = Dict[str, str]


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    siglum: str
    museum_number: str
    accession: str
    period: Period
    provenance: Provenance
    type: ManuscriptType

    def to_dict(self) -> ManuscriptDict:
        return {
            'siglum': self.siglum,
            'museumNumber': self.museum_number,
            'accession': self.accession,
            'period': self.period.long_name,
            'provenance': self.provenance.long_name,
            'type': self.type.long_name
        }


ChapterDict = Dict[str, Union[int, str, List[ManuscriptDict]]]


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification
    stage: Stage
    name: str
    order: int
    manuscripts: Tuple[Manuscript, ...] = tuple()

    def to_dict(self) -> ChapterDict:
        return {
            'classification': self.classification.value,
            'stage': self.stage.long_name,
            'name': self.name,
            'order': self.order,
            'manuscripts': [
                manuscript.to_dict()
                for manuscript in self.manuscripts
            ]
        }


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    chapters: Tuple[Chapter, ...] = tuple()

    def to_dict(self) -> Dict[str, Union[int, str, List[ChapterDict]]]:
        return {
            'category': self.category,
            'index': self.index,
            'name': self.name,
            'chapters': [chapter.to_dict() for chapter in self.chapters]
        }

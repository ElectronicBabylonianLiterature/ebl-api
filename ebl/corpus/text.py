from enum import Enum
from typing import Dict, List, Tuple, Union
import attr


class Classification(Enum):
    ANCIENT = 'Ancient'
    MODERN = 'Modern'


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


ChapterDict = Dict[str, Union[int, str]]


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification
    stage: Stage
    number: int

    def to_dict(self) -> ChapterDict:
        return {
            'classification': self.classification.value,
            'stage': self.stage.long_name,
            'number': self.number
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

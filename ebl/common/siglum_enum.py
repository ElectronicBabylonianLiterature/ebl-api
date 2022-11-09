from enum import Enum


class SiglumEnum(Enum):
    def __init__(self, long_name, abbreviation):
        self.long_name = long_name
        self.abbreviation = abbreviation

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return [enum for enum in cls if enum.abbreviation == abbreviation][0]

    @classmethod
    def from_name(cls, name):
        return [enum for enum in cls if enum.long_name == name][0]


class SiglumEnumWithParent(SiglumEnum):
    def __init__(self, long_name, abbreviation, parent):
        super().__init__(long_name, abbreviation)
        self.parent = parent

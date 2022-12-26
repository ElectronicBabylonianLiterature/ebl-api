from enum import Enum


class SiglumEnum(Enum):
    def __init__(self, long_name, abbreviation):
        self.long_name = long_name
        self.abbreviation = abbreviation

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return next(enum for enum in cls if enum.abbreviation == abbreviation)

    @classmethod
    def from_name(cls, name):
        return next(enum for enum in cls if enum.long_name == name)


class SiglumEnumWithParent(SiglumEnum):
    def __init__(self, long_name, abbreviation, parent):
        super().__init__(long_name, abbreviation)
        self.parent = parent

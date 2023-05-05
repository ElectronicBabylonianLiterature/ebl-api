from enum import Enum


class NamedEnum(Enum):
    def __init__(self, long_name, abbreviation, sort_key=-1):
        self.long_name = long_name
        self.abbreviation = abbreviation
        self.sort_key = sort_key

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return next(enum for enum in cls if enum.abbreviation == abbreviation)

    @classmethod
    def from_name(cls, name):
        return next(enum for enum in cls if enum.long_name == name)


class NamedEnumWithParent(NamedEnum):
    def __init__(self, long_name, abbreviation, parent, sort_key=-1):
        super().__init__(long_name, abbreviation, sort_key)
        self.parent = parent

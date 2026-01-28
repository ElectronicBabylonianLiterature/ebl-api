from enum import Enum


def get_by_attribute_value(cls, attribute, value):
    try:
        return next(enum for enum in cls if getattr(enum, attribute) == value)
    except StopIteration:
        raise ValueError(f"Unknown {cls.__name__}.{attribute}: {value}")


class NamedEnum(Enum):
    def __init__(self, long_name, abbreviation, sort_key=-1):
        self.long_name = long_name
        self.abbreviation = abbreviation
        self.sort_key = sort_key

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return get_by_attribute_value(cls, "abbreviation", abbreviation)

    @classmethod
    def from_name(cls, name):
        return get_by_attribute_value(cls, "long_name", name)


class NamedEnumWithParent(NamedEnum):
    def __init__(self, long_name, abbreviation, parent, sort_key=-1):
        super().__init__(long_name, abbreviation, sort_key)
        self.parent = parent

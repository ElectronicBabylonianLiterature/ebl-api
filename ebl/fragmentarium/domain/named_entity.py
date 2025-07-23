import attr
from ebl.common.domain.named_enum import NamedEnumWithParent


class NamedEntityType(NamedEnumWithParent):
    PERSON = ("PERSON", "PER", None, 0)
    LOCATION = ("LOCATION", "LOC", None, 1)


@attr.s(auto_attribs=True, frozen=True)
class NamedEntity:
    id: str
    type: NamedEntityType

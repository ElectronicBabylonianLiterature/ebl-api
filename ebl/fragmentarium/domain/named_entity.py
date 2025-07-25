from typing import List
import attr
from ebl.common.domain.named_enum import NamedEnumWithParent


class NamedEntityType(NamedEnumWithParent):
    PERSON = ("PERSON", "PER", None, 0)
    LOCATION = ("LOCATION", "LOC", None, 1)
    YEAR = ("YEAR", "YEAR", None, 2)


@attr.s(auto_attribs=True, frozen=True)
class NamedEntity:
    id: str
    type: NamedEntityType


@attr.s(auto_attribs=True, frozen=True)
class EntityAnnotationSpan(NamedEntity):
    span: List[str]

    def to_named_entity(self) -> NamedEntity:
        return NamedEntity(id=self.id, type=self.type)

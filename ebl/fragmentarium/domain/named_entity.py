from typing import List
import attr
from ebl.common.domain.named_enum import NamedEnum


class NamedEntityType(NamedEnum):
    BUILDING_NAME = ("BUILDING_NAME", "BN")
    CELESTIAL_NAME = ("CELESTIAL_NAME", "CN")
    DIVINE_NAME = ("DIVINE_NAME", "DN")
    ETHNOS_NAME = ("ETHNOS_NAME", "EN")
    FIELD_NAME = ("FIELD_NAME", "FN")
    GEOGRAPHICAL_NAME = ("GEOGRAPHICAL_NAME", "GN")
    MONTH_NAME = ("MONTH_NAME", "MN")
    OBJECT_NAME = ("OBJECT_NAME", "ON")
    PERSONAL_NAME = ("PERSONAL_NAME", "PN")
    ROYAL_NAME = ("ROYAL_NAME", "RN")
    WATERCOURSE_NAME = ("WATERCOURSE_NAME", "WN")
    YEAR_NAME = ("YEAR_NAME", "YN")


@attr.s(auto_attribs=True, frozen=True)
class NamedEntity:
    id: str
    type: NamedEntityType


@attr.s(auto_attribs=True, frozen=True)
class EntityAnnotationSpan(NamedEntity):
    span: List[str]

    def to_named_entity(self) -> NamedEntity:
        return NamedEntity(id=self.id, type=self.type)

from enum import Enum
import attr


class MapLocationPrecision(Enum):
    EXCAVATION_AREA = "excavation-area"


class MapLocationMatchMethod(Enum):
    CURATED = "curated"
    VERIFIED_SOURCE = "verified-source"


def _to_tuple(polygon_ids: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(polygon_ids, (list, tuple)):
        raise ValueError("polygonIds must be a list or tuple.")
    return tuple(polygon_ids)


def _stripped(value: str) -> str:
    return value.strip()


@attr.s(auto_attribs=True, frozen=True)
class MapLocation:
    polygon_ids: tuple[str, ...] = attr.ib(converter=_to_tuple)
    location_precision: MapLocationPrecision
    match_method: MapLocationMatchMethod
    source: str = attr.ib(converter=_stripped)
    source_revision: str = attr.ib(converter=_stripped)

    def __attrs_post_init__(self):
        if not self.polygon_ids:
            raise ValueError("polygonIds must not be empty.")
        if len(set(self.polygon_ids)) != len(self.polygon_ids):
            raise ValueError("polygonIds must be unique.")
        if any(not polygon_id.strip() for polygon_id in self.polygon_ids):
            raise ValueError("polygonIds must not contain empty values.")
        if not self.source:
            raise ValueError("source must not be empty.")
        if not self.source_revision:
            raise ValueError("sourceRevision must not be empty.")

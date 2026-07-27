from enum import Enum

import attr


class MapLocationPrecision(Enum):
    EXCAVATION_AREA = "excavation-area"


class MapLocationMatchMethod(Enum):
    CURATED = "curated"
    VERIFIED_SOURCE = "verified-source"


@attr.s(auto_attribs=True, frozen=True)
class MapLocation:
    polygon_ids: tuple[str, ...]
    location_precision: MapLocationPrecision
    match_method: MapLocationMatchMethod
    source: str
    source_revision: str

    def __attrs_post_init__(self):
        if not self.polygon_ids:
            raise ValueError("polygonIds must not be empty.")
        if len(set(self.polygon_ids)) != len(self.polygon_ids):
            raise ValueError("polygonIds must be unique.")
        if any(not polygon_id.strip() for polygon_id in self.polygon_ids):
            raise ValueError("polygonIds must not contain empty values.")
        if not self.source.strip():
            raise ValueError("source must not be empty.")
        if not self.source_revision.strip():
            raise ValueError("sourceRevision must not be empty.")

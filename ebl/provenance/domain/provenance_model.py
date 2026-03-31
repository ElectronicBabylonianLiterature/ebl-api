import attr
from typing import Optional, Tuple


STANDARD_TEXT_PROVENANCE_ID = "STANDARD_TEXT"
STANDARD_TEXT_PROVENANCE_LONG_NAME = "Standard Text"
DEFAULT_PROVENANCE_ID = "NINEVEH"
DEFAULT_PROVENANCE_LONG_NAME = "Nineveh"
DEFAULT_PROVENANCE_ABBREVIATION = "Nin"


@attr.s(frozen=True, auto_attribs=True)
class GeoCoordinate:
    latitude: float
    longitude: float
    uncertainty_radius_km: Optional[float] = None
    notes: Optional[str] = None

    def __attrs_post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )
        if not -180 <= self.longitude <= 180:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )
        if self.uncertainty_radius_km is not None and self.uncertainty_radius_km < 0:
            raise ValueError(
                f"Uncertainty radius must be non-negative, got {self.uncertainty_radius_km}"
            )


@attr.s(frozen=True, auto_attribs=True)
class ProvenanceRecord:
    id: str
    long_name: str
    abbreviation: str
    parent: Optional[str] = None
    cigs_key: Optional[str] = None
    sort_key: int = -1
    coordinates: Optional[GeoCoordinate] = None
    polygon_coordinates: Optional[Tuple[GeoCoordinate, ...]] = None

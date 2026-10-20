from __future__ import annotations

from dataclasses import dataclass

Coordinate = dict[str, float]


@dataclass(frozen=True)
class KmlPlacemark:
    raw_name: str
    variants: tuple[str, ...]
    geometry_type: str
    point: Coordinate | None = None
    polygon: tuple[Coordinate, ...] = ()
    ignored_reason: str | None = None

    @property
    def has_usable_point(self) -> bool:
        return self.ignored_reason is None and self.point is not None

    @property
    def has_usable_polygon(self) -> bool:
        return self.ignored_reason is None and bool(self.polygon)

    @property
    def has_usable_geometry(self) -> bool:
        return self.has_usable_point or self.has_usable_polygon


@dataclass(frozen=True)
class KmlParseResult:
    kmz_path: str
    kml_file_name: str
    placemarks: tuple[KmlPlacemark, ...]


@dataclass(frozen=True)
class ProposedUpdate:
    provenance_id: str
    long_name: str
    parent: str | None
    cigs_key: str | None
    placemark_name: str
    match_tier: str
    fields: tuple[str, ...]
    coordinate: Coordinate | None
    polygon_coordinates: tuple[Coordinate, ...]
    reason_safe: str
    reason_existing_data_preserved: str


@dataclass(frozen=True)
class SkippedRecord:
    provenance_id: str
    long_name: str
    reason: str
    placemark_name: str | None = None


@dataclass(frozen=True)
class ImportPlan:
    proposed_updates: tuple[ProposedUpdate, ...]
    review_candidates: tuple[ProposedUpdate, ...]
    skipped_records: tuple[SkippedRecord, ...]
    exact_unique_matches: int
    normalized_unique_matches: int
    ambiguous_matches: int
    unmatched_provenance_records: int
    unmatched_kmz_placemarks: int


@dataclass(frozen=True)
class _MatchOutcome:
    exact_unique: int = 0
    normalized_unique: int = 0
    ambiguous: int = 0
    proposed: ProposedUpdate | None = None
    review: ProposedUpdate | None = None
    skipped: SkippedRecord | None = None
    matched_placemark: KmlPlacemark | None = None

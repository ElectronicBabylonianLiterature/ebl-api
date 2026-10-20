from __future__ import annotations

from ebl.provenance.domain.provenance_model import ProvenanceRecord
from scripts.kmz.models import Coordinate, KmlPlacemark, ProposedUpdate, SkippedRecord


def _build_update_candidate(
    record: ProvenanceRecord, placemark: KmlPlacemark, tier: str
) -> tuple[ProposedUpdate | None, SkippedRecord | None]:
    fields: list[str] = []
    coordinate = None
    polygon_coordinates: tuple[Coordinate, ...] = ()
    skip_reasons: list[str] = []

    if placemark.point:
        if record.coordinates is None:
            fields.append("coordinates")
            coordinate = placemark.point
        else:
            skip_reasons.append("already has coordinates")

    if placemark.polygon:
        if record.polygon_coordinates is None:
            fields.append("polygonCoordinates")
            polygon_coordinates = placemark.polygon
        else:
            skip_reasons.append("already has polygonCoordinates")

    if fields:
        return (
            ProposedUpdate(
                record.id,
                record.long_name,
                record.parent,
                record.cigs_key,
                placemark.raw_name,
                tier,
                tuple(fields),
                coordinate,
                polygon_coordinates,
                "Exact unique match and every target field is currently missing"
                if tier == "exact"
                else "Normalized unique match requires human review before applying",
                "Only missing field(s) are set; the update filter requires each target field to be absent or null.",
            ),
            None,
        )

    reason = (
        ", ".join(skip_reasons) if skip_reasons else "KMZ has no usable coordinates"
    )
    return None, SkippedRecord(record.id, record.long_name, reason, placemark.raw_name)

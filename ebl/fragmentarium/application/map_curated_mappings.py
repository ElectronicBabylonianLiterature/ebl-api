from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)


class CuratedMappingRecord(TypedDict):
    findspotId: int
    polygonIds: list[str]
    locationPrecision: str
    matchMethod: str
    source: str
    sourceRevision: str


class CuratedCrosswalkRow(Schema):
    findspot_id = fields.Integer(required=True, data_key="findspotId")
    site_id = fields.String(required=True, data_key="siteId")
    polygon_ids = fields.List(
        fields.String(validate=validate.Length(min=1)),
        required=True,
        data_key="polygonIds",
        validate=validate.Length(min=1),
    )
    match_method = fields.String(required=True, data_key="matchMethod")
    reviewer = fields.String(required=True, validate=validate.Length(min=1))
    review_date = fields.String(
        required=True, data_key="reviewDate", validate=validate.Length(min=1)
    )
    source = fields.String(required=True, validate=validate.Length(min=1))
    source_revision = fields.String(
        required=True, data_key="sourceRevision", validate=validate.Length(min=1)
    )
    note = fields.String(required=False, load_default="")

    @validates_schema
    def validate_row(self, data, **kwargs) -> None:
        if data.get("match_method") != "curated":
            raise ValidationError(
                "curated crosswalk rows must have matchMethod 'curated'.",
                "matchMethod",
            )
        polygon_ids = data.get("polygon_ids", ())
        if len(set(polygon_ids)) != len(polygon_ids):
            raise ValidationError("polygonIds must be unique.", "polygonIds")

    @post_load
    def to_mapping_record(self, data, **kwargs) -> CuratedMappingRecord:
        return {
            "findspotId": data["findspot_id"],
            "polygonIds": list(data["polygon_ids"]),
            "locationPrecision": "excavation-area",
            "matchMethod": "curated",
            "source": data["source"],
            "sourceRevision": data["source_revision"],
        }


def load_curated_mappings(
    path: Path | None, site_id: str, known_polygon_ids: set[str]
) -> tuple[CuratedMappingRecord, ...]:
    if path is None:
        return ()
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"Expected a JSON array of curated rows in {path}.")
    schema = CuratedCrosswalkRow()
    records: list[CuratedMappingRecord] = []
    seen_findspot_ids: set[int] = set()
    for entry in entries:
        if entry.get("siteId") != site_id:
            raise ValueError(
                f"Curated row for findspot {entry.get('findspotId')} declares "
                f"siteId {entry.get('siteId')!r}, expected {site_id!r}."
            )
        record = schema.load(entry)
        missing = [pid for pid in record["polygonIds"] if pid not in known_polygon_ids]
        if missing:
            raise ValueError(
                f"Curated row for findspot {record['findspotId']} references "
                f"unknown polygon IDs: {missing}"
            )
        if record["findspotId"] in seen_findspot_ids:
            raise ValueError(f"Duplicate curated findspot ID: {record['findspotId']}")
        seen_findspot_ids.add(record["findspotId"])
        records.append(record)
    return tuple(records)


def merge_verified_and_curated(
    verified: tuple[CuratedMappingRecord, ...],
    curated: tuple[CuratedMappingRecord, ...],
) -> tuple[CuratedMappingRecord, ...]:
    verified_ids = {record["findspotId"] for record in verified}
    curated_ids = {record["findspotId"] for record in curated}
    overlap = verified_ids & curated_ids
    if overlap:
        raise ValueError(
            f"Findspot IDs present in both verified and curated mappings: {overlap}"
        )
    return tuple(
        sorted(verified + curated, key=lambda record: int(record["findspotId"]))
    )

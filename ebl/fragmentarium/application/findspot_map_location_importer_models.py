from dataclasses import dataclass
from pathlib import Path

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validates_schema,
    validate,
)

from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.schemas import ValueEnumField


ASSUR_SITE_ID = "ASSUR"
DEFAULT_MAPPINGS_PATH = Path(
    "ebl/fragmentarium/data/map/assur_findspot_polygon_mappings.json"
)
DEFAULT_INVENTORY_PATH = Path("ebl/fragmentarium/data/map/assur_polygon_inventory.json")


@dataclass(frozen=True)
class MapLocationImportRecord:
    findspot_id: int
    map_location: MapLocation


@dataclass(frozen=True)
class ImportIssue:
    findspot_id: int | None
    reason: str


@dataclass(frozen=True)
class ImportSummary:
    scanned: int
    valid: int
    invalid: int
    unknown_findspots: int
    wrong_site: int
    unknown_polygons: int
    existing: int
    new: int
    changed: int
    skipped: int
    applied: int
    dry_run: bool
    rollback: bool
    issues: tuple[ImportIssue, ...]
    database_classification: str = "local"
    total_findspots: int | None = None
    assur_findspots: int | None = None
    unresolved_assur_findspots: int | None = None


class MapLocationImportRecordSchema(Schema):
    findspot_id = fields.Integer(required=True, data_key="findspotId")
    polygon_ids = fields.List(
        fields.String(validate=validate.Length(min=1)),
        required=True,
        data_key="polygonIds",
        validate=validate.Length(min=1),
    )
    location_precision = ValueEnumField(
        MapLocationPrecision, required=True, data_key="locationPrecision"
    )
    match_method = ValueEnumField(
        MapLocationMatchMethod, required=True, data_key="matchMethod"
    )
    source = fields.String(required=True, validate=validate.Length(min=1))
    source_revision = fields.String(
        required=True, data_key="sourceRevision", validate=validate.Length(min=1)
    )

    @validates_schema
    def validate_record(self, data, **kwargs) -> None:
        polygon_ids = data.get("polygon_ids", ())
        if len(set(polygon_ids)) != len(polygon_ids):
            raise ValidationError("polygonIds must be unique.", "polygonIds")
        if any(not polygon_id.strip() for polygon_id in polygon_ids):
            raise ValidationError(
                "polygonIds must not contain empty values.", "polygonIds"
            )
        if not data.get("source", "").strip():
            raise ValidationError("source must not be empty.", "source")
        if not data.get("source_revision", "").strip():
            raise ValidationError("sourceRevision must not be empty.", "sourceRevision")

    @post_load
    def create_record(self, data, **kwargs) -> MapLocationImportRecord:
        data["polygon_ids"] = tuple(data["polygon_ids"])
        data["source"] = data["source"].strip()
        data["source_revision"] = data["source_revision"].strip()
        return MapLocationImportRecord(
            findspot_id=data.pop("findspot_id"),
            map_location=MapLocation(**data),
        )

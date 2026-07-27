from marshmallow import (
    EXCLUDE,
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


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class MapLocationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

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
    def validate_map_location(self, data, **kwargs) -> None:
        polygon_ids = data.get("polygon_ids", ())
        if len(set(polygon_ids)) != len(polygon_ids):
            raise ValidationError("polygonIds must be unique.", "polygonIds")
        if any(not polygon_id.strip() for polygon_id in polygon_ids):
            raise ValidationError(
                "polygonIds must not contain empty values.", "polygonIds"
            )
        if _strip_or_none(data.get("source")) is None:
            raise ValidationError("source must not be empty.", "source")
        if _strip_or_none(data.get("source_revision")) is None:
            raise ValidationError("sourceRevision must not be empty.", "sourceRevision")

    @post_load
    def create_map_location(self, data, **kwargs) -> MapLocation:
        data["polygon_ids"] = tuple(data["polygon_ids"])
        data["source"] = data["source"].strip()
        data["source_revision"] = data["source_revision"].strip()
        return MapLocation(**data)

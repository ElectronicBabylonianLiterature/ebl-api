from typing import cast

import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory


def _map_location(*polygon_ids, source="Assur Tafeln.ods", revision="2026-07-27"):
    return MapLocation(
        polygon_ids=tuple(polygon_ids),
        location_precision=MapLocationPrecision.EXCAVATION_AREA,
        match_method=MapLocationMatchMethod.VERIFIED_SOURCE,
        source=source,
        source_revision=revision,
    )


def _payload(**changes) -> dict:
    return {
        "polygonIds": ["assur-1"],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "Assur Tafeln.ods",
        "sourceRevision": "2026-07-27",
        **changes,
    }


@pytest.mark.parametrize("polygon_ids", [["assur-1"], ["assur-1", "assur-2"]])
def test_map_location_schema_round_trip(polygon_ids):
    schema = MapLocationSchema()
    payload = _payload(polygonIds=polygon_ids)

    assert schema.dump(schema.load(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        _payload(polygonIds=[]),
        _payload(polygonIds=["assur-1", "assur-1"]),
        _payload(polygonIds=["assur-1", "  "]),
        _payload(locationPrecision="not-a-precision"),
        _payload(matchMethod="not-a-method"),
        _payload(source="   "),
        _payload(sourceRevision="  "),
    ],
)
def test_map_location_schema_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        MapLocationSchema().load(payload)


def test_map_location_schema_rejects_unknown_field():
    with pytest.raises(ValidationError):
        MapLocationSchema().load(_payload(unknown="value"))


def test_findspot_schema_omits_missing_map_location(seeded_provenance_service):
    findspot = FindspotFactory.build(
        site=seeded_provenance_service.find_by_id("ASSUR"), map_location=None
    )
    schema = FindspotSchema(context={"provenance_service": seeded_provenance_service})
    dumped = cast(dict, schema.dump(findspot))

    assert "mapLocation" not in dumped
    assert schema.load(dumped) == findspot


def test_findspot_schema_round_trip_with_map_location(seeded_provenance_service):
    findspot = FindspotFactory.build(
        site=seeded_provenance_service.find_by_id("ASSUR"),
        map_location=_map_location("assur-1"),
    )
    schema = FindspotSchema(context={"provenance_service": seeded_provenance_service})

    assert schema.load(cast(dict, schema.dump(findspot))) == findspot

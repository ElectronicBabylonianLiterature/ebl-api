import attr
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


@pytest.mark.parametrize("polygon_ids", [("assur-1",), ("assur-1", "assur-2")])
def test_map_location_schema_round_trip(polygon_ids):
    schema = MapLocationSchema()
    payload = {
        "polygonIds": list(polygon_ids),
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "Assur Tafeln.ods",
        "sourceRevision": "2026-07-27",
    }
    assert schema.dump(schema.load(payload)) == payload


@pytest.mark.parametrize(
    "payload",
    [
        {
            "polygonIds": [],
            "locationPrecision": "excavation-area",
            "matchMethod": "verified-source",
            "source": "Assur Tafeln.ods",
            "sourceRevision": "2026-07-27",
        },
        {
            "polygonIds": ["assur-1", "assur-1"],
            "locationPrecision": "excavation-area",
            "matchMethod": "verified-source",
            "source": "Assur Tafeln.ods",
            "sourceRevision": "2026-07-27",
        },
        {
            "polygonIds": ["assur-1"],
            "locationPrecision": "not-a-precision",
            "matchMethod": "verified-source",
            "source": "Assur Tafeln.ods",
            "sourceRevision": "2026-07-27",
        },
        {
            "polygonIds": ["assur-1"],
            "locationPrecision": "excavation-area",
            "matchMethod": "not-a-method",
            "source": "Assur Tafeln.ods",
            "sourceRevision": "2026-07-27",
        },
    ],
)
def test_map_location_schema_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        MapLocationSchema().load(payload)


def test_findspot_schema_omits_missing_map_location(seeded_provenance_service):
    site = seeded_provenance_service.find_by_id("ASSUR")
    findspot = attr.evolve(FindspotFactory.build(site=site, map_location=None))
    schema = FindspotSchema(context={"provenance_service": seeded_provenance_service})

    assert "mapLocation" not in schema.dump(findspot)
    assert schema.load(schema.dump(findspot)).map_location is None


def test_findspot_schema_round_trip_with_map_location(seeded_provenance_service):
    site = seeded_provenance_service.find_by_id("ASSUR")
    findspot = attr.evolve(
        FindspotFactory.build(site=site, map_location=_map_location("assur-1"))
    )
    schema = FindspotSchema(context={"provenance_service": seeded_provenance_service})

    assert schema.load(schema.dump(findspot)) == findspot

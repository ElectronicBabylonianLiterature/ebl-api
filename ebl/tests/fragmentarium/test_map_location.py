import pytest

from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)


def _map_location(**changes) -> MapLocation:
    return MapLocation(
        **{
            "polygon_ids": ("assur-1",),
            "location_precision": MapLocationPrecision.EXCAVATION_AREA,
            "match_method": MapLocationMatchMethod.CURATED,
            "source": "Assur Tafeln.ods",
            "source_revision": "2026-07-27",
            **changes,
        }
    )


def test_map_location_is_created():
    map_location = _map_location(polygon_ids=("assur-1", "assur-2"))

    assert map_location.polygon_ids == ("assur-1", "assur-2")
    assert map_location.location_precision == MapLocationPrecision.EXCAVATION_AREA
    assert map_location.match_method == MapLocationMatchMethod.CURATED
    assert map_location.source == "Assur Tafeln.ods"
    assert map_location.source_revision == "2026-07-27"


def test_map_location_is_hashable():
    assert hash(_map_location()) == hash(_map_location())


def test_map_location_accepts_polygon_id_sequence():
    assert _map_location(polygon_ids=["assur-1", "assur-2"]).polygon_ids == (
        "assur-1",
        "assur-2",
    )


def test_map_location_normalizes_source_whitespace():
    map_location = _map_location(
        source="  Assur Tafeln.ods  ", source_revision=" 2026-07-27 "
    )

    assert map_location.source == "Assur Tafeln.ods"
    assert map_location.source_revision == "2026-07-27"


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"polygon_ids": ()}, "polygonIds must not be empty."),
        ({"polygon_ids": ("assur-1", "assur-1")}, "polygonIds must be unique."),
        (
            {"polygon_ids": ("assur-1", "  ")},
            "polygonIds must not contain empty values.",
        ),
        ({"source": "   "}, "source must not be empty."),
        ({"source_revision": "  "}, "sourceRevision must not be empty."),
    ],
)
def test_map_location_rejects_invalid_values(changes, message):
    with pytest.raises(ValueError, match=message):
        _map_location(**changes)

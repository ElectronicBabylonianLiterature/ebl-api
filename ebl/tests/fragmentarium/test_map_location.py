import pytest
from typing import cast

from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)


def _map_location(**changes: object) -> MapLocation:
    return MapLocation(
        **cast(
            dict,
            {
                "polygon_ids": ("assur-1",),
                "location_precision": MapLocationPrecision.EXCAVATION_AREA,
                "match_method": MapLocationMatchMethod.CURATED,
                "source": "Assur Tafeln.ods",
                "source_revision": "2026-07-27",
                **changes,
            },
        )
    )


def test_map_location_is_created() -> None:
    map_location = _map_location(polygon_ids=("assur-1", "assur-2"))

    assert map_location.polygon_ids == ("assur-1", "assur-2")
    assert map_location.location_precision == MapLocationPrecision.EXCAVATION_AREA
    assert map_location.match_method == MapLocationMatchMethod.CURATED
    assert map_location.source == "Assur Tafeln.ods"
    assert map_location.source_revision == "2026-07-27"


def test_map_location_is_hashable() -> None:
    assert hash(_map_location()) == hash(_map_location())


def test_map_location_accepts_polygon_id_sequence() -> None:
    assert _map_location(polygon_ids=["assur-1", "assur-2"]).polygon_ids == (
        "assur-1",
        "assur-2",
    )


def test_map_location_normalizes_polygon_ids() -> None:
    assert _map_location(polygon_ids=(" assur-1 ", "\tassur-2\n")).polygon_ids == (
        "assur-1",
        "assur-2",
    )


def test_map_location_normalizes_source_whitespace() -> None:
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
        ({"polygon_ids": (" assur-1 ", "assur-1")}, "polygonIds must be unique."),
        ({"polygon_ids": (1,)}, "polygonIds must contain only strings."),
        ({"polygon_ids": (None,)}, "polygonIds must contain only strings."),
        ({"polygon_ids": (["assur-1"],)}, "polygonIds must contain only strings."),
        (
            {"polygon_ids": ("assur-1", "  ")},
            "polygonIds must not contain empty values.",
        ),
        (
            {"polygon_ids": "assur-1"},
            "polygonIds must be a list or tuple.",
        ),
        (
            {"polygon_ids": {"assur-1"}},
            "polygonIds must be a list or tuple.",
        ),
        ({"source": "   "}, "source must not be empty."),
        ({"source_revision": "  "}, "sourceRevision must not be empty."),
        ({"source": 1}, "Map location source metadata must be a string."),
        ({"source_revision": None}, "Map location source metadata must be a string."),
    ],
)
def test_map_location_rejects_invalid_values(changes: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _map_location(**changes)

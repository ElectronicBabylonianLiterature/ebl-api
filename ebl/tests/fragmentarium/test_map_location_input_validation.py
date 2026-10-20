import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.map_location_schema import MapLocationSchema


def map_payload(**changes: object) -> dict[str, object]:
    return {
        "polygonIds": ["assur-1"],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "Assur Tafeln.ods",
        "sourceRevision": "2026-07-27",
        **changes,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"polygonIds": ["assur-1", " assur-1 "]},
        {"polygonIds": [" "]},
        {"source": " "},
        {"sourceRevision": " "},
        {"unexpected": True},
    ],
)
def test_map_location_rejects_invalid_normalized_input(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        MapLocationSchema().load(map_payload(**changes))


def test_map_location_input_normalizes_join_keys_and_metadata() -> None:
    schema = MapLocationSchema()
    location = schema.load(
        map_payload(
            polygonIds=[" assur-1 "],
            source=" Assur Tafeln.ods ",
            sourceRevision=" 2026-07-27 ",
        )
    )
    assert schema.dump(location) == map_payload()

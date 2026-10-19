from typing import Mapping

import falcon
import pytest

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.tests.factories.fragment import FragmentFactory


def _findspot_payload(**fields: object) -> Mapping[str, object]:
    return {"archaeology": {"findspot": {"_id": 1, **fields}}}


@pytest.mark.parametrize(
    "payload,error_field",
    [
        (
            _findspot_payload(
                mapLocation={
                    "polygonIds": ["assur-1"],
                    "locationPrecision": "excavation-area",
                    "matchMethod": "curated",
                    "source": "Assur Tafeln.ods",
                    "sourceRevision": "2026-07-27",
                }
            ),
            "mapLocation",
        ),
        (_findspot_payload(mapLocation={"polygonIds": []}), "mapLocation"),
        (_findspot_payload(mapLocation=None), "mapLocation"),
        (_findspot_payload(mapLocation="invalid"), "mapLocation"),
        (_findspot_payload(buildingType="not-a-building-type"), "buildingType"),
        ({}, "archaeology"),
        ({"archaeology": None}, "archaeology"),
        ({"archaeology": []}, "archaeology"),
        ([], "archaeology"),
        ({"archaeology": {"excavationNumber": 123}}, "excavationNumber"),
        ({"archaeology": {"excavationNumber": False}}, "excavationNumber"),
    ],
)
def test_archaeology_rejects_invalid_input_without_writes(
    route_context, payload: object, error_field: str
) -> None:
    fragment: Fragment = FragmentFactory.build()
    fragment_number = route_context.fragmentarium.create(fragment)
    fragments_before = list(route_context.database["fragments"].find({}))
    changelog_before = list(route_context.database["changelog"].find({}))

    result = route_context.client.simulate_post(
        f"/fragments/{fragment_number}/archaeology",
        json=payload,
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert error_field in result.json["description"]
    assert list(route_context.database["fragments"].find({})) == fragments_before
    assert list(route_context.database["changelog"].find({})) == changelog_before


def test_guest_cannot_update_archaeology(guest_client, fragmentarium, database) -> None:
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    fragments_before = list(database["fragments"].find({}))
    changelog_before = list(database["changelog"].find({}))

    result = guest_client.simulate_post(
        f"/fragments/{fragment_number}/archaeology",
        json={"archaeology": {"findspotId": 1}},
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert list(database["fragments"].find({})) == fragments_before
    assert list(database["changelog"].find({})) == changelog_before

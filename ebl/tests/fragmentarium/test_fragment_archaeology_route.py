import json
from dataclasses import dataclass
from typing import cast

import attr

import falcon
import pytest
from ebl.fragmentarium.application.archaeology_schemas import ArchaeologySchema
from ebl.fragmentarium.domain.archaeology import (
    Archaeology,
    ExcavationNumber,
)
from ebl.tests.factories.provenance import DEFAULT_PROVENANCES
from ebl.fragmentarium.domain.fragment import Fragment

from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.archaeology import DateRangeFactory, FindspotFactory
from ebl.tests.factories.fragment import FragmentFactory
from falcon import testing
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.users.domain.user import User
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)


KALHU = next(record for record in DEFAULT_PROVENANCES if record.id == "KALHU")
NIPPUR = next(record for record in DEFAULT_PROVENANCES if record.id == "NIPPUR")

ARCHAEOLOGY = Archaeology(ExcavationNumber("F", "1"), KALHU)
ARCHAEOLOGIES = [
    ARCHAEOLOGY,
    attr.evolve(ARCHAEOLOGY, site=None),
    attr.evolve(ARCHAEOLOGY, excavation_number=None),
    attr.evolve(ARCHAEOLOGY, findspot_id=None),
    attr.evolve(ARCHAEOLOGY, site=NIPPUR),
    attr.evolve(ARCHAEOLOGY, regular_excavation=False),
    attr.evolve(ARCHAEOLOGY, excavation_date=DateRangeFactory.build()),
    attr.evolve(ARCHAEOLOGY, findspot_id=1),
]


@dataclass(frozen=True)
class UpdateArchaeologyDependencies:
    client: testing.TestClient
    fragmentarium: Fragmentarium
    user: User
    provenance_service: ProvenanceService


@pytest.fixture
def update_archaeology_dependencies(
    request: pytest.FixtureRequest,
) -> UpdateArchaeologyDependencies:
    return UpdateArchaeologyDependencies(
        client=request.getfixturevalue("client"),
        fragmentarium=request.getfixturevalue("fragmentarium"),
        user=request.getfixturevalue("user"),
        provenance_service=request.getfixturevalue("seeded_provenance_service"),
    )


@pytest.mark.parametrize("old_archaeology", ARCHAEOLOGIES)
@pytest.mark.parametrize("new_archaeology", ARCHAEOLOGIES)
def test_update_archaeology(
    update_archaeology_dependencies: UpdateArchaeologyDependencies,
    old_archaeology: Archaeology,
    new_archaeology: Archaeology,
) -> None:
    client = update_archaeology_dependencies.client
    fragmentarium = update_archaeology_dependencies.fragmentarium
    user = update_archaeology_dependencies.user
    seeded_provenance_service = update_archaeology_dependencies.provenance_service
    fragment: Fragment = FragmentFactory.build(archaeology=old_archaeology)
    fragment_number = fragmentarium.create(fragment)
    data = cast(
        dict,
        ArchaeologySchema(
            context={"provenance_service": seeded_provenance_service}
        ).dump(new_archaeology),
    )

    if number := new_archaeology.excavation_number:
        data["excavationNumber"] = str(number)

    post_result = cast(
        testing.Result,
        client.simulate_post(
            f"/fragments/{fragment_number}/archaeology",
            body=json.dumps({"archaeology": data}),
        ),
    )
    expected_json = {
        **create_response_dto(
            fragment.set_archaeology(new_archaeology),
            user,
            fragment.number == "K.1",
            [],
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = cast(
        testing.Result, client.simulate_get(f"/fragments/{fragment_number}")
    )
    assert get_result.json == {**expected_json, "realiaInfo": []}


def test_fragment_get_surfaces_findspot_map_location(
    client: testing.TestClient,
    fragmentarium: Fragmentarium,
    findspot_repository: MongoFindspotRepository,
    seeded_provenance_service: ProvenanceService,
) -> None:
    findspot = FindspotFactory.build(
        id_=4242,
        site=seeded_provenance_service.find_by_id("ASSUR"),
        map_location=MapLocation(
            ("assur-1", "assur-2"),
            MapLocationPrecision.EXCAVATION_AREA,
            MapLocationMatchMethod.CURATED,
            "Assur Tafeln.ods",
            "2026-07-27",
        ),
    )
    findspot_repository.create(findspot)
    fragment: Fragment = FragmentFactory.build(
        archaeology=attr.evolve(ARCHAEOLOGY, site=None, findspot=None, findspot_id=None)
    )
    fragment_number = fragmentarium.create(fragment)

    post_result = cast(
        testing.Result,
        client.simulate_post(
            f"/fragments/{fragment_number}/archaeology",
            json={"archaeology": {"findspotId": findspot.id_}},
        ),
    )
    get_result = cast(
        testing.Result, client.simulate_get(f"/fragments/{fragment_number}")
    )

    assert post_result.status == falcon.HTTP_OK
    assert get_result.status == falcon.HTTP_OK
    assert cast(dict, post_result.json)["archaeology"]["findspotId"] == findspot.id_
    assert cast(dict, get_result.json)["archaeology"]["findspot"]["mapLocation"] == {
        "polygonIds": ["assur-1", "assur-2"],
        "locationPrecision": "excavation-area",
        "matchMethod": "curated",
        "source": "Assur Tafeln.ods",
        "sourceRevision": "2026-07-27",
    }


def test_invalid_excavation_number_update(
    client: testing.TestClient, fragmentarium: Fragmentarium, user: User
) -> None:
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    invalid_number = "colorless green ideas sleep furiously"
    invalid_data = {"excavationNumber": invalid_number}

    post_result = cast(
        testing.Result,
        client.simulate_post(
            f"/fragments/{fragment_number}/archaeology",
            body=json.dumps({"archaeology": invalid_data}),
        ),
    )
    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        "description": f"{invalid_number!r} is not a valid museum number.",
        "title": "422 Unprocessable Entity",
    }

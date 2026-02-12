import json
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

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.archaeology import DateRangeFactory
from ebl.tests.factories.fragment import FragmentFactory


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


@pytest.mark.parametrize("old_archaeology", ARCHAEOLOGIES)
@pytest.mark.parametrize("new_archaeology", ARCHAEOLOGIES)
def test_update_archaeology(
    client, fragmentarium, user, seeded_provenance_service, old_archaeology, new_archaeology
):
    fragment: Fragment = FragmentFactory.build(archaeology=old_archaeology)
    fragment_number = fragmentarium.create(fragment)
    data = ArchaeologySchema(
        context={"provenance_service": seeded_provenance_service}
    ).dump(new_archaeology)

    if number := new_archaeology.excavation_number:
        data["excavationNumber"] = str(number)

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/archaeology",
        body=json.dumps({"archaeology": data}),
    )
    expected_json = {
        **create_response_dto(
            fragment.set_archaeology(new_archaeology),
            user,
            fragment.number == "K.1",
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json


def test_invalid_excavation_number_update(client, fragmentarium, user):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    invalid_number = "colorless green ideas sleep furiously"
    invalid_data = {"excavationNumber": invalid_number}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/archaeology",
        body=json.dumps({"archaeology": invalid_data}),
    )
    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        "description": f"{invalid_number!r} is not a valid museum number.",
        "title": "422 Unprocessable Entity",
    }

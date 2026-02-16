import falcon
import pytest
import json
from ebl.fragmentarium.domain.date import DateSchema

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import (
    FragmentFactory,
    DateFactory,
    YearFactory,
    MonthFactory,
)


@pytest.mark.parametrize(
    "currentDate, updatedDate",
    [
        (
            DateFactory.build(month=MonthFactory.build(value="10")),
            DateFactory.build(month=MonthFactory.build(value="3", is_intercalary=True)),
        ),
        (
            DateFactory.build(is_seleucid_era=True),
            DateFactory.build(is_seleucid_era=False),
        ),
        (
            DateFactory.build(year=YearFactory.build(value="19")),
            DateFactory.build(year=YearFactory.build(value="7")),
        ),
        (
            None,
            DateFactory.build(),
        ),
        (
            DateFactory.build(),
            None,
        ),
    ],
)
def test_update_date(client, fragmentarium, user, currentDate, updatedDate):
    fragment = FragmentFactory.build(date=currentDate)
    fragment_number = fragmentarium.create(fragment)
    update = {"date": DateSchema().dump(updatedDate)}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/date",
        body=json.dumps(update) if updatedDate else "{}",
    )
    expected_json = create_response_dto(
        fragment.set_date(updatedDate), user, fragment.number == "K.1"
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json


def test_update_invalid_date(client, fragmentarium, user, database):
    fragment = FragmentFactory.build(date=DateFactory(year=None))
    fragment_number = fragmentarium.create(fragment)
    updates = {"date": "nonsense date"}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/date", body=json.dumps(updates)
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "Invalid date data: 'nonsense date'",
    }

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == expected_json

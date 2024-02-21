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
    fragment = FragmentFactory.build(dates_in_text=[currentDate] if currentDate else [])
    fragment_number = fragmentarium.create(fragment)
    update = {"datesInText": [DateSchema().dump(updatedDate)]}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/dates-in-text",
        body=json.dumps(update) if updatedDate else '{"datesInText": []}',
    )
    expected_json = create_response_dto(
        fragment.set_dates_in_text([updatedDate] if updatedDate else []),
        user,
        fragment.number == "K.1",
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json


def test_update_invalid_dates_in_text(client, fragmentarium, user, database):
    fragment = FragmentFactory.build(dates_in_text=[DateFactory(year=None)])
    fragment_number = fragmentarium.create(fragment)
    updates = {"datesInText": ["nonsense date"]}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/dates-in-text", body=json.dumps(updates)
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "Invalid datesInText data: '['nonsense date']'",
    }

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == expected_json

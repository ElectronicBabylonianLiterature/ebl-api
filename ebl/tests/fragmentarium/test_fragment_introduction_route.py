import json

import falcon
import pytest

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "old_introduction": "",
            "new_introduction": "A new introduction",
        },
        {
            "old_introduction": "An old introduction",
            "new_introduction": "",
        },
        {
            "old_introduction": "",
            "new_introduction": "",
        },
    ],
)
def test_update_introduction(client, fragmentarium, user, database, parameters):
    fragment = FragmentFactory.build(introduction=parameters["old_introduction"])
    fragment_number = fragmentarium.create(fragment)
    updates = {"introduction": parameters["new_introduction"]}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/introduction", body=json.dumps(updates)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_introduction(updates["introduction"]),
            user,
            fragment.number == "K.1",
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json

    assert database["changelog"].find_one(
        {
            "resource_id": fragment_number,
            "resource_type": "fragments",
            "user_profile.name": user.profile["name"],
        }
    )

import json

import falcon  # pyre-ignore

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import  FragmentFactory


def test_update_genre(client, fragmentarium, user, database):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = [["ARCHIVES", "Administrative", "Lists"]]
    body = json.dumps(update)
    post_result = client.simulate_post(f"/fragments/{fragment_number}/genre", body=body)

    expected_json = {
        **create_response_dto(
            fragment.set_genre(update),
            user,
            fragment.number == "K.1",
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
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

import json

import falcon  # pyre-ignore
import pytest  # pyre-ignore

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory


@pytest.mark.parametrize(
    "parameters", [
        {
            "currentGenre": [],
            "newGenre": [["ARCHIVES", "Administrative", "Lists"]]
        },
        {
            "currentGenre": [["ARCHIVES", "Administrative", "Lists"]],
            "newGenre": [["ARCHIVES", "Administrative", "Lists"], ["CANONICAL", "Catalogues"]]
        }
    ]
)
def test_update_genre(client, fragmentarium, user, database, parameters):
    fragment = FragmentFactory.build(genre=parameters["currentGenre"])
    fragment_number = fragmentarium.create(fragment)
    updates = {
        "genre": parameters["newGenre"]
    }

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/genre",
        body=json.dumps(updates)
    )

    expected_json = {
        **create_response_dto(
            fragment.set_genre(updates["genre"]),
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

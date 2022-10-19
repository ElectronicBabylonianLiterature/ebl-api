import json

import falcon
import pytest

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.markup import StringPart


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "old_introduction": (StringPart(""),),
            "new_introduction": (StringPart("A new introduction"),),
        },
        {
            "old_introduction": (StringPart("An old introduction"),),
            "new_introduction": (StringPart(""),),
        },
        {
            "old_introduction": (StringPart(""),),
            "new_introduction": (StringPart(""),),
        },
    ],
)
def test_update_introduction(client, fragmentarium, user, database, parameters):
    fragment = FragmentFactory.build(introduction=parameters["old_introduction"])
    fragment_number = fragmentarium.create(fragment)
    update = {
        "introduction": "".join(part.value for part in parameters["new_introduction"])
    }
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/introduction", body=json.dumps(update)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_introduction(parameters["new_introduction"]),
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

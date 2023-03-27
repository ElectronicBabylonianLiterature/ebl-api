import json

import falcon
import pytest
from ebl.fragmentarium.domain.fragment import Introduction, Fragment

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.markup import StringPart


@pytest.mark.parametrize(
    "old_introduction,new_introduction",
    [
        [
            Introduction(),
            Introduction(
                "A new introduction",
                (StringPart("A new introduction"),),
            ),
        ],
        [
            Introduction(
                "An old introduction",
                (StringPart("An old introduction"),),
            ),
            Introduction(),
        ],
        [
            Introduction(),
            Introduction(),
        ],
    ],
)
def test_update_introduction(
    client, fragmentarium, user, database, old_introduction, new_introduction
):
    fragment: Fragment = FragmentFactory.build(introduction=old_introduction)
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": new_introduction.text}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/introduction", body=json.dumps(update)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_introduction(new_introduction.text),
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


def test_update_invalid_introduction(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/introduction", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

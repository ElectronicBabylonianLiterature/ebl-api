import json

import falcon
import pytest

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    NOTES_FIXTURE,
    simulate_post_with_retry,
    find_changelog_entry,
)


@pytest.mark.parametrize("old_notes,new_notes", NOTES_FIXTURE)
def test_update_notes(client, fragmentarium, user, database, old_notes, new_notes):
    fragment: Fragment = FragmentFactory.build(notes=old_notes)
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": new_notes.text}
    post_result = simulate_post_with_retry(
        client,
        f"/fragments/{fragment_number}/edition",
        json.dumps(update),
    )
    expected_json = {
        **create_response_dto(
            fragment.set_notes(new_notes.text),
            user,
            fragment.number == "K.1",
            [],
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == {**expected_json, "realiaInfo": []}

    assert find_changelog_entry(
        database,
        {
            "resource_id": fragment_number,
            "resource_type": "fragments",
            "user_profile.name": user.profile["name"],
        },
    )


def test_update_invalid_notes(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

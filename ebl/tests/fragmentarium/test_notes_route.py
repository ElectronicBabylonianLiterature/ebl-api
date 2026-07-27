import json

import falcon
import pytest

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.route_test_context import RouteContext
from ebl.tests.fragmentarium.transliterations_route_test_helpers import NOTES_FIXTURE


@pytest.mark.parametrize("notes", NOTES_FIXTURE)
def test_update_notes(route_context: RouteContext, notes):
    old_notes, new_notes = notes
    fragment: Fragment = FragmentFactory.build(notes=old_notes)
    fragment_number = route_context.create(fragment)

    post_result = route_context.post_edition(fragment_number, {"notes": new_notes.text})
    expected_json = create_response_dto(
        fragment.set_notes(new_notes.text),
        route_context.user,
        fragment.number == "K.1",
        [],
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = route_context.get_fragment(fragment_number)
    assert get_result.json == {**expected_json, "realiaInfo": []}

    assert route_context.has_changelog_entry(fragment_number)


def test_update_invalid_notes(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

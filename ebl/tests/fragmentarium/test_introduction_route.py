import json

import falcon
import pytest
from freezegun import freeze_time

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.route_test_context import RouteContext
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    INTRO_FIXTURE,
    NOTES_FIXTURE,
)


@pytest.mark.parametrize("introduction", INTRO_FIXTURE)
def test_update_introduction(route_context: RouteContext, introduction):
    old_introduction, new_introduction = introduction
    fragment: Fragment = FragmentFactory.build(introduction=old_introduction)
    fragment_number = route_context.create(fragment)

    post_result = route_context.post_edition(
        fragment_number, {"introduction": new_introduction.text}
    )
    expected_json = create_response_dto(
        fragment.set_introduction(new_introduction.text),
        route_context.user,
        fragment.number == "K.1",
        [],
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = route_context.get_fragment(fragment_number)
    assert get_result.json == {**expected_json, "realiaInfo": []}

    assert route_context.has_changelog_entry(fragment_number)


def test_update_invalid_introduction(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("introduction", INTRO_FIXTURE)
@pytest.mark.parametrize("notes", NOTES_FIXTURE)
@pytest.mark.parametrize("new_transliteration", ["", "$ (the transliteration)"])
@freeze_time("2018-09-07 15:41:24.032")
def test_update_multiple_fields(
    route_context: RouteContext, introduction, notes, new_transliteration
):
    old_introduction, new_introduction = introduction
    old_notes, new_notes = notes
    fragment: Fragment = FragmentFactory.build(
        introduction=old_introduction, notes=old_notes
    )
    fragment_number = route_context.create(fragment)
    updates = {
        "introduction": new_introduction.text,
        "notes": new_notes.text,
        "transliteration": new_transliteration,
    }

    post_result = route_context.post_edition(fragment_number, updates)
    expected_json = create_response_dto(
        fragment.set_introduction(new_introduction.text)
        .set_notes(new_notes.text)
        .update_transliteration(
            TransliterationUpdate(parse_atf_lark(updates["transliteration"])),
            route_context.user,
        ),
        route_context.user,
        fragment.number == "K.1",
        [],
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = route_context.get_fragment(fragment_number)
    assert get_result.json == {**expected_json, "realiaInfo": []}

    assert route_context.has_changelog_entry(fragment_number)

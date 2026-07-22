import json

import falcon
import pytest
from freezegun import freeze_time

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    INTRO_FIXTURE,
    NOTES_FIXTURE,
    simulate_post_with_retry,
    find_changelog_entry,
)


@pytest.mark.parametrize("old_introduction,new_introduction", INTRO_FIXTURE)
def test_update_introduction(
    client, fragmentarium, user, database, old_introduction, new_introduction
):
    fragment: Fragment = FragmentFactory.build(introduction=old_introduction)
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": new_introduction.text}
    post_result = simulate_post_with_retry(
        client,
        f"/fragments/{fragment_number}/edition",
        json.dumps(update),
    )
    expected_json = create_response_dto(
        fragment.set_introduction(new_introduction.text),
        user,
        fragment.number == "K.1",
        [],
    )

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


def test_update_invalid_introduction(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("old_introduction,new_introduction", INTRO_FIXTURE)
@pytest.mark.parametrize("old_notes,new_notes", NOTES_FIXTURE)
@pytest.mark.parametrize("new_transliteration", ["", "$ (the transliteration)"])
@freeze_time("2018-09-07 15:41:24.032")
def test_update_multiple_fields(
    client,
    fragmentarium,
    user,
    database,
    old_introduction,
    new_introduction,
    old_notes,
    new_notes,
    new_transliteration,
):
    fragment: Fragment = FragmentFactory.build(
        introduction=old_introduction, notes=old_notes
    )
    fragment_number = fragmentarium.create(fragment)
    updates = {
        "introduction": new_introduction.text,
        "notes": new_notes.text,
        "transliteration": new_transliteration,
    }
    post_result = simulate_post_with_retry(
        client,
        f"/fragments/{fragment_number}/edition",
        json.dumps(updates),
    )
    expected_json = create_response_dto(
        fragment.set_introduction(new_introduction.text)
        .set_notes(new_notes.text)
        .update_transliteration(
            TransliterationUpdate(parse_atf_lark(updates["transliteration"])),
            user,
        ),
        user,
        fragment.number == "K.1",
        [],
    )

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

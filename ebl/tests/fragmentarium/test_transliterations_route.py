import json
import attr

import falcon
import pytest
from freezegun import freeze_time

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.fragment import Notes, Introduction, Fragment
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.fragmentarium.domain.joins import Join
from ebl.transliteration.domain.markup import StringPart, EmphasisPart


NOTES_FIXTURE = [
    [Notes(), Notes("Some notes", (StringPart("Some notes"),))],
    [Notes(), Notes()],
    [Notes("Different notes"), Notes()],
    [
        Notes("Different notes"),
        Notes(
            "Different notes @i{with emphasis}",
            (StringPart("Different notes "), EmphasisPart("with emphasis")),
        ),
    ],
]

INTRO_FIXTURE = [
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
]


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(client, fragmentarium, user, database):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    updates = {"transliteration": "$ (the transliteration)"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/edition"
    post_result = client.simulate_post(url, body=body)

    expected_json = {
        **create_response_dto(
            fragment.update_transliteration(
                TransliterationUpdate(parse_atf_lark(updates["transliteration"])),
                user,
            ),
            user,
            fragment.number == MuseumNumber("K", "1"),
        ),
        "signs": "",
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment.number}")
    assert get_result.json == expected_json

    assert database["changelog"].find_one(
        {
            "resource_id": str(fragment.number),
            "resource_type": "fragments",
            "user_profile.name": user.profile["name"],
        }
    )


@freeze_time("2018-09-07 15:41:24.032")
@pytest.mark.parametrize(
    "new_transliteration", ["2'. [...] GI₆ mu u₄-š[u ...]", "$ single ruling"]
)
def test_update_transliteration_merge_lemmatization(
    new_transliteration,
    client,
    fragmentarium,
    signs,
    sign_repository,
    transliteration_factory,
    parallel_line_injector,
    user,
):
    for sign in signs:
        sign_repository.create(sign)
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(lemmatized_fragment)
    lines = lemmatized_fragment.text.atf.split("\n")
    lines[1] = new_transliteration
    updates = {"transliteration": "\n".join(lines)}
    updated_transliteration = transliteration_factory.create(updates["transliteration"])
    updated_fragment = lemmatized_fragment.update_transliteration(
        updated_transliteration, user
    )
    expected_fragment = attr.evolve(
        updated_fragment,
        text=attr.evolve(
            updated_fragment.text,
            lines=parallel_line_injector.inject(updated_fragment.text.lines),
        ),
    )
    expected_json = create_response_dto(
        expected_fragment,
        user,
        lemmatized_fragment.number == MuseumNumber("K", "1"),
    )

    post_result = client.simulate_post(
        f"/fragments/{lemmatized_fragment.number}/edition",
        body=json.dumps(updates),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    updated_fragment = client.simulate_get(
        f"/fragments/{lemmatized_fragment.number}"
    ).json
    assert updated_fragment == expected_json


def test_update_transliteration_invalid_atf(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    updates = {"transliteration": "1. kururu"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/edition"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        "title": "422 Unprocessable Entity",
        "description": "Invalid transliteration",
        "errors": [{"description": "Invalid value", "lineNumber": 1}],
    }


def test_update_transliteration_not_lowest_join(client, fragment_repository) -> None:
    number = MuseumNumber("X", "2")
    fragment = FragmentFactory.build(number=number)
    fragment_repository.create_join([[Join(number)], [Join(MuseumNumber("X", "1"))]])
    updates = {"transliteration": "1. kururu"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/edition"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        "title": "422 Unprocessable Entity",
        "description": "Invalid transliteration",
        "errors": [{"description": "Invalid value", "lineNumber": 1}],
    }


def test_update_transliteration_not_found(client):
    url = "/fragments/unknown.fragment/edition"
    body = json.dumps({"transliteration": "$ (the transliteration)"})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_transliteration_invalid(client):
    url = "/fragments/invalid/edition"
    body = json.dumps({"transliteration": ""})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "body",
    [
        "transliteration",
        '"transliteration"',
        json.dumps(
            {
                "transliteration": "$ (the transliteration)",
                "foobar": "unexpected field",
            }
        ),
    ],
)
def test_update_transliteration_invalid_entity(client, fragmentarium, body):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/edition"

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


@pytest.mark.parametrize("old_notes,new_notes", NOTES_FIXTURE)
def test_update_notes(client, fragmentarium, user, database, old_notes, new_notes):
    fragment: Fragment = FragmentFactory.build(notes=old_notes)
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": new_notes.text}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_notes(new_notes.text),
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


def test_update_invalid_notes(client, fragmentarium, user, database):
    fragment: Fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": "@i{syntax error"}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("old_introduction,new_introduction", INTRO_FIXTURE)
def test_update_introduction(
    client, fragmentarium, user, database, old_introduction, new_introduction
):
    fragment: Fragment = FragmentFactory.build(introduction=old_introduction)
    fragment_number = fragmentarium.create(fragment)
    update = {"introduction": new_introduction.text}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(update)
    )
    expected_json = create_response_dto(
        fragment.set_introduction(new_introduction.text),
        user,
        fragment.number == "K.1",
    )

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
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/edition", body=json.dumps(updates)
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
    )

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

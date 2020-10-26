import json

import falcon  # pyre-ignore
import pytest  # pyre-ignore
from freezegun import freeze_time  # pyre-ignore

from ebl.fragmentarium.application.line_to_vec_updater import create_line_to_vec
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(client, fragmentarium, user, database):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    updates = {"transliteration": "$ (the transliteration)", "notes": "some notes"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/transliteration"
    post_result = client.simulate_post(url, body=body)

    updated_fragment = fragment.update_transliteration(
        TransliterationUpdate(
            parse_atf_lark(updates["transliteration"]), updates["notes"]
        ),
        user,
    )

    expected_json = {
        **create_response_dto(
            updated_fragment.set_line_to_vec(create_line_to_vec(updated_fragment.text.lines)),
            user,
            fragment.number == MuseumNumber("K", "1"),
        ),
        "signs": "",
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
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
def test_update_transliteration_line_to_vec(
    client, fragmentarium, signs, sign_repository, transliteration_factory, user
):

    for sign in signs:
        sign_repository.create(sign)
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(lemmatized_fragment)
    lines = lemmatized_fragment.text.atf.split("\n")
    lines[1] = "2'. [...] GI₆ mu u₄-š[u ...]"
    updates = {"transliteration": "\n".join(lines), "notes": lemmatized_fragment.notes}
    updated_transliteration = transliteration_factory.create(
        updates["transliteration"], updates["notes"]
    )
    update_lemmatized_fragment = lemmatized_fragment.update_transliteration(updated_transliteration, user)

    expected_json = create_response_dto(
        update_lemmatized_fragment.set_line_to_vec(create_line_to_vec(update_lemmatized_fragment.text.lines)),
        user,
        lemmatized_fragment.number == MuseumNumber("K", "1"),
    )

    post_result = client.simulate_post(
        f"/fragments/{lemmatized_fragment.number}/transliteration",
        body=json.dumps(updates),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    updated_fragment = client.simulate_get(
        f"/fragments/{lemmatized_fragment.number}"
    ).json
    assert updated_fragment == expected_json


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration_merge_lemmatization(
    client, fragmentarium, signs, sign_repository, transliteration_factory, user
):

    for sign in signs:
        sign_repository.create(sign)
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(lemmatized_fragment)
    lines = lemmatized_fragment.text.atf.split("\n")
    lines[1] = "2'. [...] GI₆ mu u₄-š[u ...]"
    updates = {"transliteration": "\n".join(lines), "notes": lemmatized_fragment.notes}
    updated_transliteration = transliteration_factory.create(
        updates["transliteration"], updates["notes"]
    )
    update_lemmatized_fragment = lemmatized_fragment.update_transliteration(
        updated_transliteration, user)

    expected_json = create_response_dto(
        update_lemmatized_fragment.set_line_to_vec(
            create_line_to_vec(update_lemmatized_fragment.text.lines)),
        user,
        lemmatized_fragment.number == MuseumNumber("K", "1"),
    )


    post_result = client.simulate_post(
        f"/fragments/{lemmatized_fragment.number}/transliteration",
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
    updates = {"transliteration": "1. kururu", "notes": ""}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/transliteration"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        "title": "422 Unprocessable Entity",
        "description": "Invalid transliteration",
        "errors": [{"description": "Invalid value", "lineNumber": 1}],
    }


def test_update_transliteration_not_found(client):
    url = "/fragments/unknown.fragment/transliteration"
    body = json.dumps(
        {"transliteration": "$ (the transliteration)", "notes": "some notes"}
    )
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_transliteration_invalid(client):
    url = "/fragments/invalud/transliteration"
    body = json.dumps({"transliteration": "", "notes": ""})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "body",
    [
        "transliteration",
        '"transliteration"',
        json.dumps({"transliteration": "$ (the transliteration)"}),
        json.dumps({"notes": "some notes"}),
        json.dumps({"transliteration": 1, "notes": "some notes"}),
        json.dumps({"transliteration": "$ (the transliteration)", "notes": 1}),
    ],
)
def test_update_transliteration_invalid_entity(client, fragmentarium, body):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/transliteration"

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST

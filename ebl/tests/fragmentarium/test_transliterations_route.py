import json
import attr

import falcon
import pytest
from freezegun import freeze_time

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.fragmentarium.domain.joins import Join


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(client, fragmentarium, user, database):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    updates = {"transliteration": "$ (the transliteration)"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/transliteration"
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
    updates = {"transliteration": "1. kururu"}
    body = json.dumps(updates)
    url = f"/fragments/{fragment.number}/transliteration"
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
    body = json.dumps({"transliteration": "$ (the transliteration)"})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_transliteration_invalid(client):
    url = "/fragments/invalud/transliteration"
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
    url = f"/fragments/{fragment.number}/transliteration"

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST

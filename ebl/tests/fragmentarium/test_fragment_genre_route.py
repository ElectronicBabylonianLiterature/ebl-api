import json

import falcon
import pytest

from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.fragment import Genre
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "currentGenres": (),
            "newGenres": [Genre(["ARCHIVAL", "Administrative", "Lists"], False)],
        },
        {
            "currentGenres": (Genre(["ARCHIVAL", "Administrative", "Lists"], False),),
            "newGenres": [
                Genre(["ARCHIVAL", "Administrative", "Lists"], False),
                Genre(["ARCHIVAL", "Administrative", "Memos"], False),
            ],
        },
        {
            "currentGenres": (Genre(["ARCHIVAL", "Administrative", "Lists"], False),),
            "newGenres": [],
        },
    ],
)
def test_update_genres(client, fragmentarium, user, database, parameters):
    fragment = FragmentFactory.build(genres=parameters["currentGenres"])
    fragment_number = fragmentarium.create(fragment)
    updates = {"genres": GenreSchema().dump(parameters["newGenres"], many=True)}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/genres", body=json.dumps(updates)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_genres(updates["genres"]), user, fragment.number == "K.1"
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


def test_update_invalid_genres(client, fragmentarium, user, database):
    fragment = FragmentFactory.build(genres=())
    fragment_number = fragmentarium.create(fragment)
    updates = {"genres": [{"category": ["asd", "wtz"], "uncertain": False}]}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/genres", body=json.dumps(updates)
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "'('asd', 'wtz')' is not a valid genre",
    }

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == expected_json

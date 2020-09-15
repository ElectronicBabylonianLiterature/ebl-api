import falcon  # pyre-ignore

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_get(client, fragmentarium, user):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    result = client.simulate_get(f"/fragments/{transliterated_fragment.number}")

    assert result.json == create_response_dto(
        transliterated_fragment,
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
    )
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_invalid_id(client):
    result = client.simulate_get("/fragments/invalid-number")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_not_found(client):
    result = client.simulate_get("/fragments/unknown.number")

    assert result.status == falcon.HTTP_NOT_FOUND

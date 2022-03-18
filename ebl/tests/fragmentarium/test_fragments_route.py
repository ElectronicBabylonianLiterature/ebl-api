import falcon

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import ParallelFragment, ParallelText


def test_get(client, fragmentarium, user):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    result = client.simulate_get(f"/fragments/{transliterated_fragment.number}")

    expected = create_response_dto(
        transliterated_fragment,
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
    )
    for line in expected["text"]["lines"]:
        if line["type"] in (ParallelFragment.__name__, ParallelText.__name__):
            line["exists"] = False

    assert result.json == expected
    assert result.status == falcon.HTTP_OK


def test_get_invalid_id(client):
    result = client.simulate_get("/fragments/invalid-number")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_not_found(client):
    result = client.simulate_get("/fragments/unknown.number")

    assert result.status == falcon.HTTP_NOT_FOUND

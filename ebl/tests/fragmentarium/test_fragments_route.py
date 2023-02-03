import pytest
import attr
import falcon

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from urllib.parse import urlencode


@pytest.mark.parametrize(
    "lines_parameter,lines_slice",
    [
        ([], (0, None)),
        (
            ["0", "1"],
            (0, 2),
        ),
        (
            "1",
            (1, 2),
        ),
    ],
)
def test_get(
    client, fragmentarium, parallel_line_injector, user, lines_parameter, lines_slice
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    query_parameters = f"?{urlencode({'lines': lines_parameter}, doseq=True)}"

    result = client.simulate_get(
        f"/fragments/{transliterated_fragment.number}{query_parameters}"
    )

    start, end = lines_slice
    text_lines = transliterated_fragment.text.lines

    expected_fragment = attr.evolve(
        transliterated_fragment,
        text=attr.evolve(
            transliterated_fragment.text,
            lines=parallel_line_injector.inject(
                text_lines[start : end or len(text_lines)]
            )
            or text_lines,
        ),
    )
    expected = create_response_dto(
        expected_fragment,
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
    )

    assert result.json == expected
    assert result.status == falcon.HTTP_OK


def test_get_invalid_lines(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(
        f"/fragments/{transliterated_fragment.number}?lines=invalidtest"
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "lines must be a list of integers, got ['invalidtest'] instead",
    }

    assert result.json == expected_json
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_invalid_id(client):
    result = client.simulate_get("/fragments/invalid-number")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_not_found(client):
    result = client.simulate_get("/fragments/unknown.number")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_guest_scope(guest_client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = guest_client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_OK

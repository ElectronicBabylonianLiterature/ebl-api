import attr
import falcon

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_get(client, fragmentarium, parallel_line_injector, user):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    result = client.simulate_get(f"/fragments/{transliterated_fragment.number}")

    expected_fragment = attr.evolve(
        transliterated_fragment,
        text=attr.evolve(
            transliterated_fragment.text,
            lines=parallel_line_injector.inject(transliterated_fragment.text.lines),
        ),
    )
    expected = create_response_dto(
        expected_fragment,
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
    )

    assert result.json == expected
    assert result.status == falcon.HTTP_OK


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

    assert result.status == falcon.HTTP_FORBIDDEN


def test_get_fragment_no_access(basic_fragmentarium_permissions_client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = basic_fragmentarium_permissions_client.simulate_get(
        f"/fragments/{fragment.number}"
    )

    assert result.status == falcon.HTTP_FORBIDDEN

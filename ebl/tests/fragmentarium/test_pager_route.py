import falcon
import pytest

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory


@pytest.mark.parametrize("current", [0, 1, 2])
def test_get_fragment_pager(client, fragmentarium, current):
    for index in range(3):
        fragmentarium.create(
            FragmentFactory.build(number=MuseumNumber("X", str(index))), sort_key=index
        )

    result = client.simulate_get(f"/fragments/X.{current}/pager")

    assert result.json == {
        "previous": f"X.{(current - 1) % 3}",
        "next": f"X.{(current + 1) % 3}",
    }
    assert result.status == falcon.HTTP_OK


def test_get_fragment_pager_cache(cached_client, fragmentarium):
    fragment_0 = FragmentFactory.build(number=MuseumNumber("X", "0"))
    fragment_1 = FragmentFactory.build(number=MuseumNumber("X", "3"))
    for fragment in [fragment_0, fragment_1]:
        fragmentarium.create(fragment)

    first_result = cached_client.simulate_get(f"/fragments/{fragment_1.number}/pager")
    fragmentarium.create(FragmentFactory.build(number=MuseumNumber("X", "2")))
    second_result = cached_client.simulate_get(f"/fragments/{fragment_1.number}/pager")

    assert first_result.json == second_result.json
    assert first_result.status == second_result.status


def test_get_fragment_pager_invalid_id(client):
    result = client.simulate_get("/fragments/invalid/pager")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_folio_pager(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = client.simulate_get(f"/fragments/{fragment.number}/pager/WGL/1")

    assert result.json == {
        "next": {"fragmentNumber": str(fragment.number), "folioNumber": "1"},
        "previous": {"fragmentNumber": str(fragment.number), "folioNumber": "1"},
    }
    assert result.status == falcon.HTTP_OK


def test_get_folio_pager_invalid_id(client):
    result = client.simulate_get("/fragments/invalid/pager/WGL/1")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

import falcon  # pyre-ignore

from ebl.tests.factories.fragment import FragmentFactory
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_get_fragment_pager(client, fragmentarium):
    fragment = FragmentFactory.build(number=MuseumNumber("X", "1"))
    fragmentarium.create(fragment)
    result = client.simulate_get(f"/fragments/{fragment.number}/pager")

    assert result.json == {
        "next": "X.1",
        "previous": "X.1",
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


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
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_folio_pager_invalid_id(client):
    result = client.simulate_get("/fragments/invalid/pager/WGL/1")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_folio_pager_no_access_to_folio(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = client.simulate_get(f"/fragments/{fragment.number}/pager/XXX/1")

    assert result.status == falcon.HTTP_FORBIDDEN

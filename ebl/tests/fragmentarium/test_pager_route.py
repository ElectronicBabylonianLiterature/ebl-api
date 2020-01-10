import falcon

from ebl.tests.factories.fragment import FragmentFactory


def test_get_fragment_pager(client, fragmentarium):
    fragment = FragmentFactory.build(number="1")
    fragment_number = fragmentarium.of_single(fragment)
    result = client.simulate_get(f"/fragments/{fragment_number}/pager")

    assert result.json == {
        "next": "1",
        "previous": "1",
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_folio_pager(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.of_single(fragment)
    result = client.simulate_get(f"/fragments/{fragment_number}/pager/WGL/1")

    assert result.json == {
        "next": {"fragmentNumber": fragment_number, "folioNumber": "1"},
        "previous": {"fragmentNumber": fragment_number, "folioNumber": "1"},
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_image_no_access(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.of_single(fragment)
    result = client.simulate_get(f"/fragments/{fragment_number}/pager/XXX/1")

    assert result.status == falcon.HTTP_FORBIDDEN

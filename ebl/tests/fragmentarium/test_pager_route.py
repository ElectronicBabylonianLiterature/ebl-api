import falcon

from ebl.tests.factories.fragment import FragmentFactory


def test_get_folio_pager(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/pager/folios/WGL/1/{fragment_number}')

    assert result.json == {
        'next': {
            'fragmentNumber': fragment_number,
            'folioNumber': '1'
        },
        'previous': {
            'fragmentNumber': fragment_number,
            'folioNumber': '1'
        }
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_get_image_no_access(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/pager/folios/XXX/1/{fragment_number}')

    assert result.status == falcon.HTTP_FORBIDDEN

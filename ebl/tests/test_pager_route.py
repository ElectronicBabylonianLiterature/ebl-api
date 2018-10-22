import falcon


def test_get_folio_pager(client, fragmentarium, fragment):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/pager/folios/XXX/1/{fragment_number}')

    assert result.json == {
        'next': {
            'fragment_number': fragment_number,
            'folio_number': '1'
        },
        'previous': {
            'fragment_number': fragment_number,
            'folio_number': '1'
        }
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'

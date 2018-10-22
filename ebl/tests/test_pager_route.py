import falcon


def test_get_folio_pager(client, fragmentarium, fragment):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/pager/folios/XXX/1/{fragment_number}')

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

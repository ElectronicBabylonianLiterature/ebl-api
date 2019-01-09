import falcon


def test_get_fragment(client, fragmentarium, transliterated_fragment, user):
    fragment_number = fragmentarium.create(transliterated_fragment)
    result = client.simulate_get(f'/fragments/{fragment_number}')

    assert result.json == {
        **transliterated_fragment.to_dict_for(user),
        'atf': transliterated_fragment.text.atf
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_fragment_not_found(client):
    result = client.simulate_get('/fragments/unknown.number')

    assert result.status == falcon.HTTP_NOT_FOUND

import json
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


def test_update_transliteration(client,
                                fragmentarium,
                                fragment):
    fragment_number = fragmentarium.create(fragment)
    updates = {
        'transliteration': '$ (the transliteration)',
        'notes': 'some notes'
    }
    body = json.dumps(updates)
    url = f'/fragments/{fragment_number}'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_PERMANENT_REDIRECT
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

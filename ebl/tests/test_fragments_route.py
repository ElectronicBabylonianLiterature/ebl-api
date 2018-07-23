# pylint: disable=W0621
import json
import falcon


def test_get_fragment(client, fragmentarium, fragment):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments/{fragment_number}')

    assert json.loads(result.content) == fragment
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_fragment_not_found(client):
    result = client.simulate_get('/fragments/unknown.number')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_update_transliteration(client,
                                fragmentarium,
                                fragment,
                                fetch_user_profile):
    fragment_number = fragmentarium.create(fragment)
    updates = {
        'transliteration': 'the transliteration',
        'notes': 'some notes'
    }
    body = json.dumps(updates)
    url = f'/fragments/{fragment_number}'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/fragments/{fragment_number}')
    updated_fragment = json.loads(get_result.content)

    ebl_name = fetch_user_profile(None)['https://ebabylon.org/eblName']
    assert updated_fragment['transliteration'] == updates['transliteration']
    assert updated_fragment['notes'] == updates['notes']
    assert updated_fragment['record'][-1]['user'] == ebl_name


def test_update_transliteration_not_found(client):
    # pylint: disable=C0103
    url = '/fragments/unknown.fragment'
    post_result = client.simulate_post(url, body='"transliteration"')

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_search_fragment(client, fragmentarium, fragment):
    fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments', params={
        'number': fragment['_id']
    })

    assert json.loads(result.content) == [fragment]
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_fragment_not_found(client):
    result = client.simulate_get(f'/fragments', params={'number': 'K.1'})

    assert json.loads(result.content) == []


def test_search_word_no_query(client):
    result = client.simulate_get(f'/fragments')

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

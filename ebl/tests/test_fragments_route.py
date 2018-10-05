# pylint: disable=W0621
import json
import falcon


def test_get_fragment(client, fragmentarium, fragment):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments/{fragment_number}')

    assert result.json == fragment
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_fragment_not_found(client):
    result = client.simulate_get('/fragments/unknown.number')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_update_transliteration(client,
                                fragmentarium,
                                fragment,
                                user,
                                database):
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
    updated_fragment = get_result.json

    assert updated_fragment['transliteration'] == updates['transliteration']
    assert updated_fragment['notes'] == updates['notes']
    assert updated_fragment['record'][-1]['user'] == user.ebl_name

    assert database['changelog'].find_one({
        'resource_id': fragment_number,
        'resource_type': 'fragments',
        'user_profile.name': user.profile['name']
    })


def test_update_transliteration_not_found(client):
    # pylint: disable=C0103
    url = '/fragments/unknown.fragment'
    post_result = client.simulate_post(url, body='"transliteration"')

    assert post_result.status == falcon.HTTP_NOT_FOUND

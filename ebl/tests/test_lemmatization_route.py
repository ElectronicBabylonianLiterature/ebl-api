import json
import falcon
import pytest


def test_update_lemmatization(client,
                              fragmentarium,
                              transliterated_fragment,
                              lemmatization,
                              user,
                              database):
    # pylint: disable=R0913
    fragment_number = fragmentarium.create(transliterated_fragment)
    tokens = lemmatization.tokens
    tokens[0][0]['uniqueLemma'] = ['aklu I']
    body = json.dumps(tokens)
    url = f'/fragments/{fragment_number}/lemmatization'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/fragments/{fragment_number}')
    updated_fragment = get_result.json

    assert updated_fragment['lemmatization'] == tokens

    assert database['changelog'].find_one({
        'resource_id': fragment_number,
        'resource_type': 'fragments',
        'user_profile.name': user.profile['name']
    })


def test_update_lemmatization_not_found(client):
    url = '/fragments/unknown.fragment/lemmatization'
    body = json.dumps([[]])
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("body", [
    'lemmatization',
    '"lemmatization"',
    json.dumps({
        'lemmatization': [[{'value': 'u₄-šu', 'uniqueLemma': []}]]
    }),
    json.dumps([{'value': 'u₄-šu', 'uniqueLemma': []}]),
    json.dumps([['u₄-šu']]),
    json.dumps([[{'value': 1, 'uniqueLemma': []}]]),
    json.dumps([[{'value': 'u₄-šu', 'uniqueLemma': 1}]]),
    json.dumps([[{'value': 'u₄-šu', 'uniqueLemma': [1]}]]),
    json.dumps([[{'value': None, 'uniqueLemma': []}]])
])
def test_update_lemmatization_invalid_entity(client,
                                             fragmentarium,
                                             fragment,
                                             body):
    fragment_number = fragmentarium.create(fragment)
    url = f'/fragments/{fragment_number}/lemmatization'

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_update_lemmatization_atf_change(client,
                                         fragmentarium,
                                         transliterated_fragment,
                                         lemmatization):
    fragment_number = fragmentarium.create(transliterated_fragment)
    tokens = lemmatization.tokens
    tokens[0][0]['value'] = 'ana'
    body = json.dumps(tokens)
    url = f'/fragments/{fragment_number}/lemmatization'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

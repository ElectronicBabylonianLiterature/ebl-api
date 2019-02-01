import falcon
from ebl.fragmentarium.dtos import create_response_dto


def test_search_fragment(client, fragmentarium, fragment, user):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments', params={
        'number': fragment_number
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [create_response_dto(fragment, user)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_fragment_not_found(client):
    result = client.simulate_get(f'/fragments', params={'number': 'K.1'})

    assert result.json == []


def test_search_signs(client,
                      fragmentarium,
                      transliterated_fragment,
                      sign_list,
                      signs,
                      user):
    # pylint: disable=R0913
    fragmentarium.create(transliterated_fragment)
    for sign in signs:
        sign_list.create(sign)

    result = client.simulate_get(f'/fragments', params={
        'transliteration': 'ma-tu₂'
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [{
        **create_response_dto(
            transliterated_fragment,
            user
        ),
        'matching_lines': [
            ['6\'. [...] x mu ta-ma-tu₂']
        ]
    }]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_random(client,
                fragmentarium,
                transliterated_fragment,
                user):
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f'/fragments', params={
        'random': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [create_response_dto(transliterated_fragment, user)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_interesting(client,
                     fragmentarium,
                     interesting_fragment,
                     user):
    fragmentarium.create(interesting_fragment)

    result = client.simulate_get(f'/fragments', params={
        'interesting': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [create_response_dto(interesting_fragment, user)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_fragment_no_query(client):
    result = client.simulate_get(f'/fragments')

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_too_many_params(client):
    params = {'random': True, 'interesting': True}
    result = client.simulate_get(f'/fragments', params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_invalid_param(client):
    params = {'this_param': 'is wrong'}
    result = client.simulate_get(f'/fragments', params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

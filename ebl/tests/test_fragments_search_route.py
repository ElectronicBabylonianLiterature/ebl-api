import falcon
import pydash


def test_search_fragment(client, fragmentarium, fragment):
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments', params={
        'number': fragment_number
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [fragment.to_dict()]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_fragment_not_found(client):
    result = client.simulate_get(f'/fragments', params={'number': 'K.1'})

    assert result.json == []


def test_search_signs(client,
                      fragmentarium,
                      transliterated_fragment,
                      sign_list,
                      signs):
    fragmentarium.create(transliterated_fragment)
    for sign in signs:
        sign_list.create(sign)

    result = client.simulate_get(f'/fragments', params={
        'transliteration': 'ma-tu₂'
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        pydash.set_(transliterated_fragment.to_dict(), 'matching_lines', [
            ['6\'. [...] x mu ta-ma-tu₂']
        ])
    ]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_random(client,
                fragmentarium,
                fragment):
    fragmentarium.create(fragment)

    result = client.simulate_get(f'/fragments', params={
        'random': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [fragment.to_dict()]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_interesting(client,
                     fragmentarium,
                     fragment):
    fragmentarium.create(fragment)

    result = client.simulate_get(f'/fragments', params={
        'interesting': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [fragment.to_dict()]
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

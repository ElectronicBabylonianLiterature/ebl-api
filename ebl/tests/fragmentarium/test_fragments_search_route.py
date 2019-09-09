import falcon
from hamcrest import assert_that, has_entry, has_properties

from ebl.fragment.fragment_info import FragmentInfo
from ebl.fragmentarium.dtos import create_fragment_info_dto
from ebl.tests.factories.fragment import FragmentFactory, \
    InterestingFragmentFactory, TransliteratedFragmentFactory


def expected_fragment_info_dto(fragment):
    return create_fragment_info_dto(FragmentInfo.of(fragment))


def test_search_fragment(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f'/fragments', params={
        'number': fragment_number
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(fragment)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_search_fragment_not_found(client):
    result = client.simulate_get(f'/fragments', params={'number': 'K.1'})

    assert result.json == []


def test_search_signs(client,
                      fragmentarium,
                      sign_list,
                      signs):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    for sign in signs:
        sign_list.create(sign)

    result = client.simulate_get(f'/fragments', params={
        'transliteration': 'ma-tu₂'
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [{
        **expected_fragment_info_dto(transliterated_fragment),
        'matchingLines': [
            ['6\'. [...] x mu ta-ma-tu₂']
        ]
    }]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_random(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f'/fragments', params={
        'random': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_interesting(client, fragmentarium):
    interesting_fragment = InterestingFragmentFactory.build()
    fragmentarium.create(interesting_fragment)

    result = client.simulate_get(f'/fragments', params={
        'interesting': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(interesting_fragment)]
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_latest(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f'/fragments', params={
        'latest': True
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
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

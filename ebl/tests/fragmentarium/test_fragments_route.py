import falcon

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_get_fragment(client, fragmentarium, user):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_number = fragmentarium.create(transliterated_fragment)
    result = client.simulate_get(f'/fragments/{fragment_number}')

    assert result.json == create_response_dto(
        transliterated_fragment,
        user,
        transliterated_fragment.number == 'K.1'
    )
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_fragment_not_found(client):
    result = client.simulate_get('/fragments/unknown.number')

    assert result.status == falcon.HTTP_NOT_FOUND

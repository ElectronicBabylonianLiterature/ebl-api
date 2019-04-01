import json
import falcon
from freezegun import freeze_time
import pytest
from ebl.fragment.transliteration import Transliteration
from ebl.fragmentarium.dtos import create_response_dto


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(client,
                                fragmentarium,
                                fragment,
                                user,
                                database):
    fragment_number = fragmentarium.create(fragment)
    updates = {
        'transliteration': '$ (the transliteration)',
        'notes': 'some notes'
    }
    body = json.dumps(updates)
    url = f'/fragments/{fragment_number}/transliteration'
    post_result = client.simulate_post(url, body=body)

    expected_json = {
        **create_response_dto(
            fragment.update_transliteration(
                Transliteration(updates['transliteration'], updates['notes']),
                user
            ),
            user
        ),
        'signs': ''
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == expected_json

    get_result = client.simulate_get(f'/fragments/{fragment_number}')
    assert get_result.json == expected_json

    assert database['changelog'].find_one({
        'resource_id': fragment_number,
        'resource_type': 'fragments',
        'user_profile.name': user.profile['name']
    })


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration_merge_lemmatization(client,
                                                    fragmentarium,
                                                    lemmatized_fragment,
                                                    signs,
                                                    sign_list,
                                                    user):
    # pylint: disable=R0913
    for sign in signs:
        sign_list.create(sign)
    fragment_number = fragmentarium.create(lemmatized_fragment)
    lines = lemmatized_fragment.text.atf.split('\n')
    lines[1] = '2\'. [...] GI₆ mu u₄-š[u ...]'
    updates = {
        'transliteration': '\n'.join(lines),
        'notes': lemmatized_fragment.notes
    }
    expected_json = create_response_dto(
        lemmatized_fragment.update_transliteration(
            Transliteration(
                updates['transliteration'],
                updates['notes']
            ).with_signs(sign_list),
            user
        ),
        user
    )

    post_result = client.simulate_post(
        f'/fragments/{fragment_number}/transliteration',
        body=json.dumps(updates)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    updated_fragment =\
        client.simulate_get(f'/fragments/{fragment_number}').json
    assert updated_fragment == expected_json


def test_update_transliteration_invalid_atf(client,
                                            fragmentarium,
                                            fragment):
    fragment_number = fragmentarium.create(fragment)
    updates = {
        'transliteration': '$ this is not valid',
        'notes': ''
    }
    body = json.dumps(updates)
    url = f'/fragments/{fragment_number}/transliteration'
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == {
        'title': '422 Unprocessable Entity',
        'description': 'Invalid transliteration',
        'errors': [
            {
                'description': 'Invalid line',
                'lineNumber': 1,
            }
        ]
    }


def test_update_transliteration_not_found(client):
    url = '/fragments/unknown.fragment/transliteration'
    body = json.dumps({
        'transliteration': '$ (the transliteration)',
        'notes': 'some notes'
    })
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("body", [
    'transliteration',
    '"transliteration"',
    json.dumps({
        'transliteration': '$ (the transliteration)'
    }),
    json.dumps({
        'notes': 'some notes'
    }),
    json.dumps({
        'transliteration': 1,
        'notes': 'some notes'
    }),
    json.dumps({
        'transliteration': '$ (the transliteration)',
        'notes': 1
    })
])
def test_update_transliteration_invalid_entity(client,
                                               fragmentarium,
                                               fragment,
                                               body):
    fragment_number = fragmentarium.create(fragment)
    url = f'/fragments/{fragment_number}/transliteration'

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST

# pylint: disable=W0621
import json
import falcon
import pydash
import pytest


INVALID_ENTRIES = [
    lambda entry: {**entry, 'title': 47},
    lambda entry: pydash.omit(entry, 'type')
]


@pytest.fixture
def saved_entry(bibliography, bibliography_entry, user):
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


def test_get_entry(client, saved_entry):
    id_ = saved_entry['id']
    result = client.simulate_get(f'/bibliography/{id_}')

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_get_entry_not_found(client):
    id_ = 'not found'
    result = client.simulate_get(f'/bibliography/{id_}')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_create_entry(client, bibliography_entry):
    id_ = bibliography_entry['id']
    body = json.dumps(bibliography_entry)
    put_result = client.simulate_put(f'/bibliography', body=body)

    assert put_result.status == falcon.HTTP_OK
    assert put_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/bibliography/{id_}')

    assert get_result.json == bibliography_entry


def test_create_entry_duplicate(client, saved_entry):
    body = json.dumps(saved_entry)

    put_result = client.simulate_put(f'/bibliography', body=body)

    assert put_result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize('transform', INVALID_ENTRIES)
def test_create_entry_invalid(transform, client, bibliography_entry):
    invalid_entry = transform(bibliography_entry)
    body = json.dumps(invalid_entry)

    put_result = client.simulate_put(f'/bibliography', body=body)

    assert put_result.status == falcon.HTTP_BAD_REQUEST


def test_update_entry(client, saved_entry):
    id_ = saved_entry['id']
    updated_entry = {
        **saved_entry,
        'title': 'New Title'
    }
    body = json.dumps(updated_entry)
    post_result = client.simulate_post(f'/bibliography/{id_}', body=body)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'

    get_result = client.simulate_get(f'/bibliography/{id_}')

    assert get_result.json == updated_entry


def test_update_entry_not_found(client, bibliography_entry):
    id_ = bibliography_entry['id']
    body = json.dumps(bibliography_entry)

    post_result = client.simulate_post(f'/bibliography/{id_}', body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize('transform', [
    lambda entry: {**entry, 'title': 47},
    lambda entry: pydash.omit(entry, 'type')
])
def test_update_entry_invalid(transform, client, saved_entry):
    id_ = saved_entry['id']
    invalid_entry = transform(saved_entry)
    body = json.dumps(invalid_entry)

    post_result = client.simulate_post(f'/bibliography/{id_}', body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


@pytest.mark.parametrize('params', [
    {},
    {'author': 'Author'},
    {'year': 2019},
    {'title': 'Title'},
    {
        'author': 'Author',
        'year': 2019,
        'title': 'Title'
    }
])
def test_search(client, saved_entry, params):
    result = client.simulate_get('/bibliography', params=params)

    assert result.json == [saved_entry]
    assert result.status == falcon.HTTP_OK
    assert result.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.parametrize('params', [
    {'invalid': 'param'},
    {'year': 'invalid'}
])
def test_search_invalid_query(client, params):
    result = client.simulate_get('/bibliography', params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY

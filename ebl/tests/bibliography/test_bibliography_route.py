import json

import falcon  # pyre-ignore
import pydash  # pyre-ignore
import pytest  # pyre-ignore

INVALID_ENTRIES = [
    lambda entry: {**entry, "title": 47},
    lambda entry: pydash.omit(entry, "type"),
]


@pytest.fixture
def saved_entry(bibliography, bibliography_entry, user):
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


def test_get_entry(client, saved_entry):
    id_ = saved_entry["id"]
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_entry_not_found(client):
    id_ = "not found"
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_create_entry(client, bibliography_entry):
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)
    post_result = client.simulate_post(f"/bibliography", body=body)

    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.headers["Location"] == f"/bibliography/{id_}"
    assert post_result.json == bibliography_entry

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == bibliography_entry


def test_create_entry_duplicate(client, saved_entry):
    body = json.dumps(saved_entry)

    put_result = client.simulate_post(f"/bibliography", body=body)

    assert put_result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("transform", INVALID_ENTRIES)
def test_create_entry_invalid(transform, client, bibliography_entry):
    invalid_entry = transform(bibliography_entry)
    body = json.dumps(invalid_entry)

    put_result = client.simulate_post(f"/bibliography", body=body)

    assert put_result.status == falcon.HTTP_BAD_REQUEST


def test_update_entry(client, saved_entry):
    id_ = saved_entry["id"]
    updated_entry = {**saved_entry, "title": "New Title"}
    body = json.dumps(updated_entry)
    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NO_CONTENT
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == updated_entry


def test_update_entry_not_found(client, bibliography_entry):
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)

    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "transform",
    [lambda entry: {**entry, "title": 47}, lambda entry: pydash.omit(entry, "type"),],
)
def test_update_entry_invalid(transform, client, saved_entry):
    id_ = saved_entry["id"]
    invalid_entry = transform(saved_entry)
    body = json.dumps(invalid_entry)

    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


@pytest.mark.parametrize(
    "params",
    [
        {"query": "Author"},
        {"query": "2019"},
        {"query": "Title"},
        {"query": "Author 2019 Title"},
        {"query": "Author 1"},
        {"query": "Container-Title-Short"},
    ],
)
def test_search(client, saved_entry, params):
    result = client.simulate_get("/bibliography", params=params)

    assert result.json == [saved_entry]
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"

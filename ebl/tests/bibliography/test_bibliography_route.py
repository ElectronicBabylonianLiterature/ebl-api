import json

import falcon
import pydash
import pytest

from ebl.tests.factories.bibliography import BibliographyEntryFactory

INVALID_ENTRIES = [
    lambda entry: {**entry, "title": 47},
    lambda entry: pydash.omit(entry, "type"),
]


@pytest.fixture
def saved_entry(bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


@pytest.fixture
def saved_entries(bibliography, user):
    number_of_entries = 5
    entries = [
        BibliographyEntryFactory.build(id=f"XY{i + 1:05}")
        for i in range(number_of_entries)
    ]

    for entry in entries:
        bibliography.create(entry, user)

    return entries


def test_get_entry(client, saved_entry):
    id_ = saved_entry["id"]
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK


def test_get_entry_not_found(client):
    result = client.simulate_get("/bibliography/not found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_create_entry(client):
    bibliography_entry = BibliographyEntryFactory.build()
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)
    post_result = client.simulate_post("/bibliography", body=body)

    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers["Location"] == f"/bibliography/{id_}"
    assert post_result.json == bibliography_entry

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == bibliography_entry


def test_create_entry_duplicate(client, saved_entry):
    body = json.dumps(saved_entry)

    put_result = client.simulate_post("/bibliography", body=body)

    assert put_result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("transform", INVALID_ENTRIES)
def test_create_entry_invalid(transform, client):
    bibliography_entry = BibliographyEntryFactory.build()
    invalid_entry = transform(bibliography_entry)
    body = json.dumps(invalid_entry)

    put_result = client.simulate_post("/bibliography", body=body)

    assert put_result.status == falcon.HTTP_BAD_REQUEST


def test_update_entry(client, saved_entry):
    id_ = saved_entry["id"]
    updated_entry = {**saved_entry, "title": "New Title"}
    body = json.dumps(updated_entry)
    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NO_CONTENT

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == updated_entry


def test_update_entry_not_found(client):
    bibliography_entry = BibliographyEntryFactory.build()
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)

    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "transform",
    [lambda entry: {**entry, "title": 47}, lambda entry: pydash.omit(entry, "type")],
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
        {"query": "Miccadei"},
        {
            "query": "Miccadei 2002 The Synergistic Activity of Thyroid Transcription Factor 1"
        },
        {"query": "ME 1"},
        {"query": "ME"},
    ],
)
def test_search(client, saved_entry, params):
    result = client.simulate_get("/bibliography", params=params)

    assert result.json == [saved_entry]
    assert result.status == falcon.HTTP_OK


def test_list_all_bibliography(client, saved_entry):
    result = client.simulate_get("/bibliography/all")

    assert result.json == [saved_entry["id"]]
    assert result.status == falcon.HTTP_OK


def test_list_bibliography(client, saved_entries):
    ids = [entry["id"] for entry in saved_entries]
    result = client.simulate_get(f"/bibliography/list?ids={','.join(ids)}")

    assert result.json == saved_entries
    assert result.status == falcon.HTTP_OK

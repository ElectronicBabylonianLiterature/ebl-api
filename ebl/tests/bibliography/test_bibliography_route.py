import json

import attr
import falcon
import pydash
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.infrastructure.auth0 import Auth0User

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


def client_with_scope(context, scope: str):
    return testing.TestClient(
        ebl.app.create_app(
            attr.evolve(
                context,
                auth_backend=NoneAuthBackend(
                    lambda: Auth0User({"scope": scope}, lambda: {"name": "Test User"})
                ),
            )
        )
    )


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


def test_duplicate_candidates(client, database, saved_entry):
    proposed_entry = {**saved_entry, "id": "Q30000001"}
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["highestScore"] >= 0.92
    assert result.json["candidates"][0]["id"] == saved_entry["id"]
    assert result.json["candidates"][0]["recommendation"] == "block_or_request_override"
    assert result.json["candidates"][0]["matchedFields"]["doi"] == 1.0
    assert database["bibliography"].count_documents({}) == before_count


def test_duplicate_candidates_allows_missing_id(client, saved_entry):
    proposed_entry = pydash.omit(saved_entry, "id")
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "likely_duplicate"


def test_duplicate_candidates_invalid(client):
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps({"title": "Missing type"}),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_duplicate_candidates_requires_duplicate_check_scope(guest_client, saved_entry):
    result = guest_client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(saved_entry),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_duplicate_candidates_rejects_write_only_scope(context, saved_entry):
    client = client_with_scope(context, "write:bibliography")
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(saved_entry),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_export_page(client, saved_entries):
    first_page = client.simulate_get("/api/v1/bibliography", params={"limit": 2})

    assert first_page.status == falcon.HTTP_OK
    assert first_page.json["limit"] == 2
    assert [item["id"] for item in first_page.json["items"]] == [
        saved_entries[0]["id"],
        saved_entries[1]["id"],
    ]
    assert first_page.json["items"][0]["citationKey"] is None
    assert first_page.json["items"][0]["bibliographyEntry"] == saved_entries[0]
    assert first_page.json["nextCursor"] == saved_entries[1]["id"]

    second_page = client.simulate_get(
        "/api/v1/bibliography",
        params={"limit": 2, "cursor": first_page.json["nextCursor"]},
    )

    assert [item["id"] for item in second_page.json["items"]] == [
        saved_entries[2]["id"],
        saved_entries[3]["id"],
    ]


def test_partner_bibliography_export_caps_limit(client, saved_entries):
    result = client.simulate_get("/api/v1/bibliography", params={"limit": 999})

    assert result.status == falcon.HTTP_OK
    assert result.json["limit"] == 100


def test_partner_bibliography_entry_by_id(client, saved_entry):
    result = client.simulate_get(f"/api/v1/bibliography/{saved_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == saved_entry["id"]
    assert result.json["citationKey"] is None
    assert result.json["bibliographyEntry"] == saved_entry


def test_partner_bibliography_entry_not_found(client):
    result = client.simulate_get("/api/v1/bibliography/not-found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_export_requires_export_scope(guest_client):
    result = guest_client.simulate_get("/api/v1/bibliography")

    assert result.status == falcon.HTTP_FORBIDDEN

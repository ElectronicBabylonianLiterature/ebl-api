import json

import falcon
import pydash
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    INVALID_ENTRIES,
    client_with_scope,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_get_entry(client, saved_entry):
    id_ = saved_entry["id"]
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK


def test_get_deprecated_entry_redirects_to_canonical(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(f"/bibliography/{deprecated_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json == canonical_entry


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


def test_create_deprecated_entry_requires_redirect_target(client):
    bibliography_entry = BibliographyEntryFactory.build(deprecated=True)

    result = client.simulate_post("/bibliography", json=bibliography_entry)

    assert result.status == falcon.HTTP_BAD_REQUEST


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


def test_list_all_bibliography_excludes_deprecated(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get("/bibliography/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry["id"]]


def test_list_bibliography(client, saved_entries):
    ids = [entry["id"] for entry in saved_entries]
    result = client.simulate_get(f"/bibliography/list?ids={','.join(ids)}")

    assert result.json == saved_entries
    assert result.status == falcon.HTTP_OK


def test_list_bibliography_resolves_deprecated_ids(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/bibliography/list", params={"ids": deprecated_entry["id"]}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


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


def test_duplicate_candidates_series_sibling_is_not_likely(
    client, bibliography, user, database
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        type="book",
        title="Babylonian Provincial Officials Part One",
        author=[{"given": "Mark", "family": "Smith"}],
        issued={"date-parts": [[2010]]},
        DOI="",
        publisher="Eisenbrauns",
        **{"collection-title": "Babylonian Provincial Officials"},
    )
    proposed_entry = {
        **existing_entry,
        "id": "Q30000001",
        "title": "Babylonian Provincial Officials Part Two",
    }
    bibliography.create(existing_entry, user)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "no_duplicate"
    assert result.json["candidates"][0]["decision"] == "no_duplicate"
    assert "series_part" in result.json["candidates"][0]["conflictingFields"]
    assert database["bibliography"].count_documents({}) == before_count


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

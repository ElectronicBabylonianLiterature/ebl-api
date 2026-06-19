import json

import falcon

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    insufficient_data_duplicate_result,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


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


def test_partner_bibliography_create(client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert (
        result.headers["Location"] == f"/api/v1/bibliography/{bibliography_entry['id']}"
    )
    assert result.json == bibliography_entry

    get_result = client.simulate_get(f"/api/v1/bibliography/{bibliography_entry['id']}")

    assert get_result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_create_requires_write_scope(guest_client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = guest_client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create_rejects_export_only_scope(context):
    client = client_with_scope(context, "export:bibliography")
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create_invalid(client):
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps({"title": "Missing type"})
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_partner_bibliography_create_duplicate_conflict_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(duplicate_entry)
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["candidates"][0]["id"] == saved_entry["id"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_create_insufficient_data_conflict_does_not_mutate(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "insufficient_data"
    assert result.json["candidates"][0]["recommendation"] == "confirm_before_create"
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_create_series_sibling_does_not_conflict(
    client, bibliography, user
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
    sibling_entry = {
        **existing_entry,
        "id": "Q30000001",
        "title": "Babylonian Provincial Officials Part Two",
    }
    bibliography.create(existing_entry, user)

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(sibling_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert bibliography.find(existing_entry["id"]) == existing_entry
    assert bibliography.find(sibling_entry["id"]) == sibling_entry

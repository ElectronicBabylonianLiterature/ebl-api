import re
import json

import falcon
import pytest

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


def test_partner_bibliography_export_excludes_deprecated_records(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="Q30000000")
    deprecated_entry = BibliographyEntryFactory.build(
        id="Q30000001", deprecated=True, redirectTo=canonical_entry["id"]
    )
    active_entry = BibliographyEntryFactory.build(id="Q30000002")
    for entry in (canonical_entry, deprecated_entry, active_entry):
        bibliography.create(entry, user)

    first_page = client.simulate_get("/api/v1/bibliography", params={"limit": 1})
    second_page = client.simulate_get(
        "/api/v1/bibliography",
        params={"limit": 1, "cursor": first_page.json["nextCursor"]},
    )

    assert [item["id"] for item in first_page.json["items"]] == [canonical_entry["id"]]
    assert first_page.json["nextCursor"] == canonical_entry["id"]
    assert [item["id"] for item in second_page.json["items"]] == [active_entry["id"]]
    assert second_page.json["nextCursor"] is None


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


def test_partner_bibliography_entry_by_deprecated_id_redirects(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(f"/api/v1/bibliography/{deprecated_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == canonical_entry["id"]
    assert result.json["bibliographyEntry"] == canonical_entry


def test_partner_bibliography_entry_by_citation_key(client, bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="miccadei2002")
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(
        f"/api/v1/bibliography/{bibliography_entry['citationKey']}"
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["citationKey"] == bibliography_entry["citationKey"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_entry_by_alias(client, bibliography, user):
    alias = "legacy-id"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": alias}]
    )
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(f"/api/v1/bibliography/{alias}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_resolve_by_canonical_id(client, saved_entry):
    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": saved_entry["id"]},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == saved_entry["id"]
    assert result.json["bibliographyEntry"] == saved_entry


def test_partner_bibliography_resolve_by_deprecated_id_redirects(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": deprecated_entry["id"]},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == canonical_entry["id"]
    assert result.json["bibliographyEntry"] == canonical_entry


def test_partner_bibliography_resolve_by_normalized_duplicate_alias(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(
        id="CANONICAL_ID",
        aliases=[
            {
                "value": "DUPLICATE_ID",
                "normalizedValue": "duplicate-id",
                "type": "reviewed_duplicate_id",
                "source": "possible_dedupes.xlsx",
                "status": "redirect",
            }
        ],
    )
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve", params={"identifier": "duplicate id"}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == canonical_entry["id"]
    assert result.json["bibliographyEntry"] == canonical_entry


def test_partner_bibliography_resolve_by_citation_key(client, bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="miccadei2002")
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": bibliography_entry["citationKey"]},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["citationKey"] == bibliography_entry["citationKey"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_resolve_by_raw_slash_alias(client, bibliography, user):
    alias = "Leipzig/ABC 123"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": "leipzig-abc-123"}]
    )
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": alias},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_resolve_by_special_character_alias(
    client, bibliography, user
):
    alias = "D’Agostino"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": "d-agostino"}]
    )
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": alias},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_resolve_missing_identifier(client):
    result = client.simulate_get("/api/v1/bibliography/resolve")

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "identifier" in result.json["description"]


def test_partner_bibliography_resolve_not_found(client):
    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": "not-found"},
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_resolve_missing_redirect_target_returns_not_found(
    client, bibliography, user
):
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo="MISSING_ID"
    )
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": deprecated_entry["id"]},
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert "redirect target MISSING_ID not found" in result.json["description"]


def test_partner_bibliography_resolve_redirect_loop_returns_conflict(
    client, bibliography, user
):
    first_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_A", deprecated=True, redirectTo="DUPLICATE_B"
    )
    second_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_B", deprecated=True, redirectTo="DUPLICATE_A"
    )
    bibliography.create(first_entry, user)
    bibliography.create(second_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve", params={"identifier": first_entry["id"]}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "redirect loop" in result.json["description"]


def test_partner_bibliography_resolve_ambiguous_alias_returns_conflict(
    client, bibliography, user
):
    alias = "legacy"
    first_entry = BibliographyEntryFactory.build(
        id="Q30000001", aliases=[{"value": alias, "normalizedValue": alias}]
    )
    second_entry = BibliographyEntryFactory.build(
        id="Q30000002", aliases=[{"value": alias, "normalizedValue": alias}]
    )
    bibliography.create(first_entry, user)
    bibliography.create(second_entry, user)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": alias},
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "ambiguous" in result.json["description"]


def test_partner_bibliography_entry_not_found(client):
    result = client.simulate_get("/api/v1/bibliography/not-found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_export_requires_export_scope(guest_client):
    result = guest_client.simulate_get("/api/v1/bibliography")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_resolve_requires_export_scope(context):
    client = client_with_scope(context, "write:bibliography")

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": "Q30000000"},
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create(client):
    bibliography_entry = {
        key: value
        for key, value in BibliographyEntryFactory.build().items()
        if key != "id"
    }
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert re.fullmatch(r"Q\d{8}", result.json["id"])
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert result.json["citationKey"] == "miccadei2002Synergistic"

    get_result = client.simulate_get(f"/api/v1/bibliography/{result.json['id']}")

    assert get_result.json["id"] == result.json["id"]
    assert get_result.json["citationKey"] == "miccadei2002Synergistic"
    assert get_result.json["bibliographyEntry"] == result.json


def test_partner_bibliography_create_with_submitted_id_stores_alias(client):
    submitted_id = "partner-legacy-123"
    bibliography_entry = BibliographyEntryFactory.build(id=submitted_id)

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.json["id"] != submitted_id
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert result.json["citationKey"] == "miccadei2002Synergistic"
    assert result.json["aliases"] == [
        {
            "value": submitted_id,
            "normalizedValue": submitted_id,
            "type": "partner_id",
            "source": "partner_request",
            "status": "redirect",
        }
    ]

    canonical_result = client.simulate_get(f"/api/v1/bibliography/{result.json['id']}")
    alias_result = client.simulate_get(f"/api/v1/bibliography/{submitted_id}")

    assert canonical_result.json["bibliographyEntry"] == result.json
    assert alias_result.json["id"] == result.json["id"]
    assert alias_result.json["bibliographyEntry"] == result.json


def test_partner_bibliography_create_citation_key_collision_suffixes(
    client, bibliography, user
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        citationKey="miccadei2002Synergistic",
    )
    bibliography.create(existing_entry, user)
    submitted_id = "partner-collision-123"
    bibliography_entry = BibliographyEntryFactory.build(
        id=submitted_id,
        type="book",
        DOI="10.1000/collision",
        PMID="99999999",
        title="Synergistic Tablets from Babylon",
        publisher="Test Press",
        volume="12",
        issue="1",
        page="1-20",
    )

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.json["id"] != submitted_id
    assert result.json["citationKey"] == "miccadei2002Synergistic-2"
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert result.json["aliases"][0]["value"] == submitted_id
    assert bibliography.find(existing_entry["id"]) == existing_entry


def test_partner_bibliography_create_preserves_special_character_aliases(client):
    submitted_id = "Von_Soden:Alte/Orient"
    bibliography_entry = BibliographyEntryFactory.build(id=submitted_id)

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.json["aliases"][0]["value"] == submitted_id
    assert result.json["aliases"][0]["normalizedValue"] == "von-soden-alte-orient"

    alias_result = client.simulate_get("/api/v1/bibliography/Von Soden Alte Orient")

    assert alias_result.status == falcon.HTTP_OK
    assert alias_result.json["id"] == result.json["id"]


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


def test_partner_bibliography_create_rejects_unsafe_partner_id(client, database):
    bibliography_entry = BibliographyEntryFactory.build(id="bad\u0000id")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "control characters" in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


@pytest.mark.parametrize("partner_id", ["", "   "])
def test_partner_bibliography_create_rejects_empty_partner_id(
    partner_id, client, database
):
    bibliography_entry = BibliographyEntryFactory.build(id=partner_id)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "must be a non-empty string" in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


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


def test_partner_bibliography_create_alias_collision_returns_conflict(
    client, bibliography, user, database
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        aliases=[
            {
                "value": "Leipzig/ABC 123",
                "normalizedValue": "leipzig-abc-123",
            }
        ],
    )
    bibliography.create(existing_entry, user)
    before_count = database["bibliography"].count_documents({})
    bibliography_entry = BibliographyEntryFactory.build(
        id="Leipzig ABC 123",
        DOI="10.1000/two",
        title="A Different Title",
        issued={"date-parts": [[2005, 1, 1]]},
    )

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "already in use" in result.json["description"]
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
    assert bibliography.find(result.json["id"]) == result.json

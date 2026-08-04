import json
import re
from datetime import datetime, timedelta

import falcon
import pytest

from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


RESERVATIONS = "bibliography_lookup_reservations"


def lookup_values(entry):
    values = {entry["id"], entry["citationKey"]}
    for alias in entry.get("aliases", []):
        values.add(alias["value"])
        values.add(alias["normalizedValue"])
    return values


def test_partner_bibliography_create(client, database):
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
    reservations = database[RESERVATIONS].find(
        {"_id": {"$in": list(lookup_values(result.json))}}
    )
    assert {reservation["state"] for reservation in reservations} == {
        LookupReservationState.COMMITTED.value
    }


def test_partner_bibliography_create_with_submitted_id_stores_alias(client, database):
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
    values = lookup_values(result.json)
    assert database[RESERVATIONS].count_documents(
        {"_id": {"$in": list(values)}}
    ) == len(values)


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


def test_partner_bibliography_create_citation_key_exhaustion_returns_conflict(
    monkeypatch, client, bibliography_repository, database
):
    patch_duplicate_override_result(
        monkeypatch, {"decision": "unique", "highestScore": 0, "candidates": []}
    )
    base_key = "miccadei2002Synergistic"
    reserved_values = [base_key, *(f"{base_key}-{suffix}" for suffix in range(2, 101))]
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation(
            "owner", "Q99999999", datetime.utcnow() + timedelta(hours=1)
        ),
        reserved_values,
    )
    bibliography_entry = BibliographyEntryFactory.build(id="partner-exhausted-key")
    before_bibliography_count = database["bibliography"].count_documents({})
    before_changelog_count = database["changelog"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "Unable to generate a unique citation key" in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_bibliography_count
    assert database[RESERVATIONS].count_documents({"state": "pending"}) == len(
        reserved_values
    )
    assert database["changelog"].count_documents({}) == before_changelog_count


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

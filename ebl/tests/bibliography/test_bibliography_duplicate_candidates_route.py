import json

import falcon
import pydash

from ebl.tests.bibliography.bibliography_route_test_helpers import client_with_scope
from ebl.tests.factories.bibliography import BibliographyEntryFactory


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

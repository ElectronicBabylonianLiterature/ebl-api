import json

import falcon

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    insufficient_data_duplicate_result,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


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

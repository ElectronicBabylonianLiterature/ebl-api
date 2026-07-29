import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import client_with_scope
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def insert_legacy_entry(database, create_mongo_bibliography_entry, entry):
    database["bibliography"].insert_one(create_mongo_bibliography_entry(entry))


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
    client, database, create_mongo_bibliography_entry
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
    insert_legacy_entry(database, create_mongo_bibliography_entry, canonical_entry)
    insert_legacy_entry(database, create_mongo_bibliography_entry, deprecated_entry)

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


@pytest.mark.parametrize(
    "alias_case",
    [
        pytest.param(
            ("Leipzig/ABC 123", "leipzig-abc-123"),
            id="raw-slash",
        ),
        pytest.param(("D’Agostino", "d-agostino"), id="special-character"),
    ],
)
def test_partner_bibliography_resolve_by_alias(alias_case, client, bibliography, user):
    alias, normalized_value = alias_case
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": normalized_value}]
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


def test_resolve_path_segment_is_reserved_for_query_resolution(
    client, bibliography, user
):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="resolve")
    bibliography.create(bibliography_entry, user)

    dynamic_result = client.simulate_get("/api/v1/bibliography/resolve")
    resolver_result = client.simulate_get(
        "/api/v1/bibliography/resolve", params={"identifier": "resolve"}
    )

    assert dynamic_result.status == falcon.HTTP_BAD_REQUEST
    assert resolver_result.status == falcon.HTTP_OK
    assert resolver_result.json["id"] == bibliography_entry["id"]


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
    client, database, create_mongo_bibliography_entry
):
    alias = "legacy"
    first_entry = BibliographyEntryFactory.build(
        id="Q30000001", aliases=[{"value": alias, "normalizedValue": alias}]
    )
    second_entry = BibliographyEntryFactory.build(
        id="Q30000002", aliases=[{"value": alias, "normalizedValue": alias}]
    )
    insert_legacy_entry(database, create_mongo_bibliography_entry, first_entry)
    insert_legacy_entry(database, create_mongo_bibliography_entry, second_entry)

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": alias},
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "ambiguous" in result.json["description"]


def test_partner_bibliography_resolve_requires_export_scope(context):
    client = client_with_scope(context, "write:bibliography")

    result = client.simulate_get(
        "/api/v1/bibliography/resolve",
        params={"identifier": "Q30000000"},
    )

    assert result.status == falcon.HTTP_FORBIDDEN

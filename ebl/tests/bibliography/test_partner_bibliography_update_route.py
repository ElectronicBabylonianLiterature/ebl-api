import json

import falcon
import pydash

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    insufficient_data_duplicate_result,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_partner_bibliography_update(client, saved_entry):
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_NO_CONTENT

    get_result = client.simulate_get(f"/api/v1/bibliography/{saved_entry['id']}")

    assert get_result.json["bibliographyEntry"] == updated_entry


def test_partner_bibliography_update_requires_write_scope(guest_client, saved_entry):
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = guest_client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_update_rejects_export_only_scope(context, saved_entry):
    client = client_with_scope(context, "export:bibliography")
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_update_not_found(client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography/Q30000001", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_update_invalid(client, saved_entry):
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}",
        body=json.dumps(pydash.omit(saved_entry, "type")),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_partner_bibliography_update_duplicate_conflict_does_not_mutate(
    client, bibliography, user
):
    existing_entry = BibliographyEntryFactory.build(id="Q30000001", DOI="10.1000/one")
    target_entry = BibliographyEntryFactory.build(id="Q30000002", DOI="10.1000/two")
    bibliography.create(existing_entry, user)
    bibliography.create(target_entry, user)
    duplicate_update = {**target_entry, "DOI": existing_entry["DOI"]}

    result = client.simulate_post(
        f"/api/v1/bibliography/{target_entry['id']}",
        body=json.dumps(duplicate_update),
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["candidates"][0]["id"] == existing_entry["id"]
    assert bibliography.find(target_entry["id"]) == target_entry


def test_partner_bibliography_update_insufficient_data_conflict_does_not_mutate(
    monkeypatch, client, bibliography, user
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    target_entry = BibliographyEntryFactory.build(id="Q30000002")
    bibliography.create(target_entry, user)
    updated_entry = {**target_entry, "title": "Sparse candidate"}

    result = client.simulate_post(
        f"/api/v1/bibliography/{target_entry['id']}",
        body=json.dumps(updated_entry),
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "insufficient_data"
    assert bibliography.find(target_entry["id"]) == target_entry


def test_partner_bibliography_delete_not_supported(client, saved_entry):
    result = client.simulate_delete(f"/api/v1/bibliography/{saved_entry['id']}")

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED

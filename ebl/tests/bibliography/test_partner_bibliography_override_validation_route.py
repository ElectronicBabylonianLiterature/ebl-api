import json

import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID,
    NON_BLOCKING_DUPLICATE_CANDIDATE_ID,
    STALE_DUPLICATE_CANDIDATE_ID,
    assert_duplicate_override_bad_request,
    blocking_duplicate_override_result,
    client_with_scope,
    duplicate_override_payload,
    insufficient_data_duplicate_result,
    mixed_duplicate_override_result,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_partner_bibliography_duplicate_override_missing_override_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        {"bibliographyEntry": duplicate_entry},
    )


def test_partner_bibliography_duplicate_override_whitespace_reason_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, [saved_entry["id"]], "   "),
        description_substring="override.reason",
    )


def test_partner_bibliography_duplicate_override_short_reason_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, [saved_entry["id"]], "too short"),
        description_substring="10 meaningful characters",
    )


@pytest.mark.parametrize(
    "payload",
    [
        lambda entry, candidate_id: {
            "bibliographyEntry": entry,
            "override": {"reason": "Reviewed returned duplicate candidates carefully."},
        },
        lambda entry, candidate_id: duplicate_override_payload(entry, []),
    ],
)
def test_partner_bibliography_duplicate_override_requires_reviewed_candidate_ids(
    payload, client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        payload(duplicate_entry, saved_entry["id"]),
    )


def test_partner_bibliography_duplicate_override_rejects_stale_candidate_ids(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, ["Q39999999"]),
        description_substring="must match the current duplicate candidates",
    )


def test_partner_bibliography_duplicate_override_rejects_only_non_blocking_candidate_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, mixed_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(
            bibliography_entry, [NON_BLOCKING_DUPLICATE_CANDIDATE_ID]
        ),
        description_substring="current blocking duplicate candidate",
    )


def test_partner_bibliography_duplicate_override_rejects_stale_candidate_after_rerun(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, blocking_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(bibliography_entry, [STALE_DUPLICATE_CANDIDATE_ID]),
        description_substring="must match the current duplicate candidates",
    )


def test_partner_bibliography_duplicate_override_unique_entry_uses_normal_create(
    client, database
):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(duplicate_override_payload(bibliography_entry, ["Q39999999"])),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "Use POST /api/v1/bibliography instead." in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_invalid_csl_does_not_mutate(
    client, database
):
    assert_duplicate_override_bad_request(
        client,
        database,
        {
            "bibliographyEntry": {"id": "Q30000001", "title": "Missing type"},
            "override": {
                "reason": (
                    "Reviewed returned duplicate candidates and confirmed this is "
                    "a distinct bibliography record."
                ),
                "reviewedCandidateIds": ["Q30000000"],
            },
        },
    )


def test_partner_bibliography_duplicate_override_rejects_unsafe_partner_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    bibliography_entry = BibliographyEntryFactory.build(id="bad\u0000id")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                bibliography_entry, [INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID]
            )
        ),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "control characters" in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_alias_collision_does_not_mutate(
    monkeypatch, client, bibliography, user, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
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
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                bibliography_entry, [INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID]
            )
        ),
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "already in use" in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_requires_write_scope(
    guest_client, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = guest_client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_duplicate_override_rejects_duplicate_check_only_scope(
    context, saved_entry
):
    client = client_with_scope(context, "check:bibliography_duplicates")
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_duplicate_override_rejects_export_only_scope(
    context, saved_entry
):
    client = client_with_scope(context, "export:bibliography")
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN

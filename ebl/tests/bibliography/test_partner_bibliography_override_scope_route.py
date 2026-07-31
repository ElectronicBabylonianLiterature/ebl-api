import json

import falcon

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    duplicate_override_payload,
)


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

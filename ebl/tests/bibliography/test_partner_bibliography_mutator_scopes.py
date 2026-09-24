import json

import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    duplicate_override_payload,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.mark.parametrize(
    ("route", "payload", "expected_status"),
    [
        (
            "/api/v1/bibliography",
            {
                "id": "partner-create-write-only",
                "type": "book",
                "title": "Unique write-scope entry",
            },
            falcon.HTTP_CREATED,
        ),
        (
            "/api/v1/bibliography/Q30000000",
            BibliographyEntryFactory.build(id="Q30000000", title="Updated"),
            falcon.HTTP_NO_CONTENT,
        ),
        (
            "/api/v1/bibliography/duplicate-override",
            duplicate_override_payload(
                BibliographyEntryFactory.build(id="partner-override-write-only"),
                ["Q30000000"],
            ),
            falcon.HTTP_CREATED,
        ),
    ],
)
def test_partner_mutators_accept_write_scope_without_export(
    context, saved_entry, route, payload, expected_status
):
    client = client_with_scope(context, "write:bibliography")

    result = client.simulate_post(route, body=json.dumps(payload))

    assert result.status == expected_status


def test_partner_create_accepts_write_and_export_scopes(context):
    client = client_with_scope(context, "write:bibliography export:bibliography")
    payload = BibliographyEntryFactory.build(id="partner-both-scopes")

    result = client.simulate_post("/api/v1/bibliography", body=json.dumps(payload))

    assert result.status == falcon.HTTP_CREATED

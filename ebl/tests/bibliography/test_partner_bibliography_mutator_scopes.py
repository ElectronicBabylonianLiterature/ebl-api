import json

import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    client_with_scope,
    duplicate_override_payload,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.mark.parametrize(
    ("route", "payload"),
    [
        (
            "/api/v1/bibliography",
            BibliographyEntryFactory.build(id="partner-create-write-only"),
        ),
        (
            "/api/v1/bibliography/Q30000000",
            BibliographyEntryFactory.build(id="Q30000000", title="Updated"),
        ),
        (
            "/api/v1/bibliography/duplicate-override",
            duplicate_override_payload(
                BibliographyEntryFactory.build(id="partner-override-write-only"),
                ["Q30000000"],
            ),
        ),
    ],
)
def test_partner_mutators_accept_write_scope_without_export(
    context, saved_entry, route, payload
):
    client = client_with_scope(context, "write:bibliography")

    result = client.simulate_post(route, body=json.dumps(payload))

    assert result.status != falcon.HTTP_FORBIDDEN

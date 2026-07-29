import json

import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID,
    duplicate_override_payload,
    insufficient_data_duplicate_result,
    patch_duplicate_override_result,
)
from ebl.errors import DataError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

SERVER_OWNED_FIELDS = ("aliases", "deprecated", "redirectTo", "citationKey")


def payload_with_server_owned_field(entry: dict, field: str) -> dict:
    values = {
        "aliases": [{"value": "partner-controlled-alias"}],
        "deprecated": True,
        "redirectTo": "Q30000001",
        "citationKey": "partnerControlledKey",
    }
    return {**entry, field: values[field]}


@pytest.mark.parametrize("field", SERVER_OWNED_FIELDS)
def test_partner_bibliography_create_rejects_server_owned_fields(
    field, client, database
):
    entry = payload_with_server_owned_field(BibliographyEntryFactory.build(), field)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post("/api/v1/bibliography", body=json.dumps(entry))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert database["bibliography"].count_documents({}) == before_count


@pytest.mark.parametrize("field", SERVER_OWNED_FIELDS)
def test_partner_bibliography_duplicate_override_rejects_server_owned_fields(
    field, monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    entry = payload_with_server_owned_field(BibliographyEntryFactory.build(), field)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                entry, [INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID]
            )
        ),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert database["bibliography"].count_documents({}) == before_count


def test_create_partner_entry_rejects_server_owned_fields_when_schema_is_bypassed(
    bibliography, user, database
):
    entry = BibliographyEntryFactory.build(
        id="partner-controlled-id",
        aliases=[{"value": "partner-controlled-alias"}],
        citationKey="partnerControlledKey",
        deprecated=True,
        redirectTo="Q39999999",
    )

    before_count = database["bibliography"].count_documents({})

    with pytest.raises(DataError):
        bibliography.create_partner_entry(entry, user)

    assert database["bibliography"].count_documents({}) == before_count

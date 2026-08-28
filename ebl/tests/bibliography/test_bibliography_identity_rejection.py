import falcon
import pydash
import pytest

from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


SERVER_OWNED_PAYLOADS = {
    "aliases": [{"value": "attacker-alias", "normalizedValue": "attacker-alias"}],
    "citationKey": "different",
    "deprecated": False,
    "redirectTo": "other-record",
}


@pytest.mark.parametrize("field", sorted(SERVER_OWNED_PAYLOADS))
def test_update_rejects_submitted_server_owned_field(
    field, client, bibliography, aliased_entry
):
    payload = {
        **metadata_only_payload(aliased_entry),
        field: SERVER_OWNED_PAYLOADS[field],
    }

    result = post_entry(client, payload)

    assert result.status == falcon.HTTP_CONFLICT
    assert field in result.text


@pytest.mark.parametrize("field", sorted(SERVER_OWNED_PAYLOADS))
def test_rejected_server_owned_field_leaves_record_unchanged(
    field, client, bibliography, aliased_entry
):
    payload = {
        **metadata_only_payload(aliased_entry),
        field: SERVER_OWNED_PAYLOADS[field],
    }

    post_entry(client, payload)
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry["aliases"] == [PARTNER_ALIAS]
    assert stored_entry["citationKey"] == CITATION_KEY
    assert stored_entry["title"] == aliased_entry["title"]
    assert stored_entry.get("deprecated") is None
    assert stored_entry.get("redirectTo") is None


def test_update_cannot_tombstone_an_active_record(client, bibliography, aliased_entry):
    payload = {
        **metadata_only_payload(aliased_entry),
        "deprecated": True,
        "redirectTo": "other-record",
    }

    result = post_entry(client, payload)
    stored_entry = bibliography.find(aliased_entry["id"])

    assert result.status == falcon.HTTP_CONFLICT
    assert "deprecated" in result.text
    assert stored_entry.get("deprecated") is None
    assert stored_entry.get("redirectTo") is None


def test_update_rejects_deprecating_without_a_redirect_target(client, aliased_entry):
    payload = {**metadata_only_payload(aliased_entry), "deprecated": True}

    result = post_entry(client, payload)

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_update_cannot_steal_an_alias_from_another_record(
    client, bibliography, user, aliased_entry
):
    other_entry = BibliographyEntryFactory.build(id="Q30000099", title="Other")
    bibliography.create(other_entry, user)
    payload = {
        **pydash.omit(other_entry, "aliases", "citationKey"),
        "aliases": [PARTNER_ALIAS],
    }

    result = post_entry(client, payload)

    assert result.status == falcon.HTTP_CONFLICT
    assert bibliography.find(PARTNER_ALIAS["value"])["id"] == aliased_entry["id"]
    assert "aliases" not in bibliography.find(other_entry["id"])

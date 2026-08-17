import falcon
import pydash
import pytest

from ebl.errors import DataError, NotFoundError
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    CORRECTED_TITLE,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_metadata_update_preserves_aliases_and_citation_key(
    client, bibliography, aliased_entry
):
    payload = metadata_only_payload(aliased_entry)

    result = post_entry(client, payload)

    assert result.status == falcon.HTTP_NO_CONTENT
    assert bibliography.find(aliased_entry["id"]) == {
        **payload,
        "aliases": [PARTNER_ALIAS],
        "citationKey": CITATION_KEY,
    }


@pytest.mark.parametrize("alias_key", ["value", "normalizedValue"])
def test_metadata_update_keeps_alias_resolvable(
    alias_key, client, bibliography, aliased_entry
):
    post_entry(client, metadata_only_payload(aliased_entry))

    assert bibliography.find(PARTNER_ALIAS[alias_key])["id"] == aliased_entry["id"]


def test_metadata_update_keeps_citation_key_resolvable(
    client, bibliography, aliased_entry
):
    post_entry(client, metadata_only_payload(aliased_entry))

    assert bibliography.find(CITATION_KEY)["id"] == aliased_entry["id"]


def test_metadata_update_keeps_record_active(client, bibliography, aliased_entry):
    post_entry(client, metadata_only_payload(aliased_entry))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry.get("deprecated") is None
    assert stored_entry.get("redirectTo") is None
    assert stored_entry["title"] == CORRECTED_TITLE


def test_metadata_update_applies_requested_metadata(
    client, bibliography, aliased_entry
):
    payload = {**metadata_only_payload(aliased_entry), "volume": "99"}

    post_entry(client, payload)

    assert bibliography.find(aliased_entry["id"])["volume"] == "99"


def test_update_ignores_submitted_aliases(client, bibliography, aliased_entry):
    payload = {
        **metadata_only_payload(aliased_entry),
        "aliases": [{"value": "attacker-alias", "normalizedValue": "attacker-alias"}],
    }

    post_entry(client, payload)

    assert bibliography.find(aliased_entry["id"])["aliases"] == [PARTNER_ALIAS]


def test_update_ignores_submitted_citation_key(client, bibliography, aliased_entry):
    payload = {**metadata_only_payload(aliased_entry), "citationKey": "different"}

    post_entry(client, payload)

    assert bibliography.find(aliased_entry["id"])["citationKey"] == CITATION_KEY


def test_update_cannot_deprecate_an_active_record(client, bibliography, aliased_entry):
    payload = {
        **metadata_only_payload(aliased_entry),
        "deprecated": True,
        "redirectTo": "other-record",
    }

    post_entry(client, payload)
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry.get("deprecated") is None
    assert stored_entry.get("redirectTo") is None


def test_update_cannot_steal_an_alias_from_another_record(
    client, bibliography, user, aliased_entry
):
    other_entry = BibliographyEntryFactory.build(id="Q30000099", title="Other")
    bibliography.create(other_entry, user)
    payload = {
        **pydash.omit(other_entry, "aliases", "citationKey"),
        "aliases": [PARTNER_ALIAS],
    }

    post_entry(client, payload)

    assert bibliography.find(PARTNER_ALIAS["value"])["id"] == aliased_entry["id"]
    assert "aliases" not in bibliography.find(other_entry["id"])


def test_legacy_record_without_identity_fields_updates_normally(
    client, bibliography, saved_entry
):
    payload = {**saved_entry, "title": "Legacy corrected"}

    result = post_entry(client, payload)
    stored_entry = bibliography.find(saved_entry["id"])

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored_entry == payload


def test_legacy_record_update_does_not_invent_identity_fields(
    client, bibliography, saved_entry
):
    post_entry(client, {**saved_entry, "title": "Legacy corrected"})
    stored_entry = bibliography.find(saved_entry["id"])

    assert "aliases" not in stored_entry
    assert "citationKey" not in stored_entry
    assert "deprecated" not in stored_entry
    assert "redirectTo" not in stored_entry


@pytest.mark.parametrize("entry", [{}, {"id": ""}, {"id": None}, {"id": 47}])
def test_update_without_a_usable_id_is_rejected(entry, bibliography, user):
    with pytest.raises(DataError, match="id is required"):
        bibliography.update({**entry, "type": "book"}, user)


def test_update_of_unknown_id_is_not_found(bibliography, user):
    with pytest.raises(NotFoundError):
        bibliography.update({"id": "does-not-exist", "type": "book"}, user)

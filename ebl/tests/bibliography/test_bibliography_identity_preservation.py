import falcon
import pytest

from ebl.errors import DataError, NotFoundError
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    CORRECTED_TITLE,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
    reservations,
)


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


@pytest.mark.parametrize(
    "unknown_field,value", [("DPO", "10.1086/719864"), ("pages", "129-143")]
)
def test_update_preserves_unknown_persisted_fields(
    unknown_field, value, client, database, saved_entry
):
    database["bibliography"].update_one(
        {"_id": saved_entry["id"]}, {"$set": {unknown_field: value}}
    )

    result = post_entry(client, {**saved_entry, "title": "Legacy corrected"})
    stored_entry = database["bibliography"].find_one({"_id": saved_entry["id"]})

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored_entry[unknown_field] == value
    assert stored_entry["title"] == "Legacy corrected"


def test_update_does_not_accept_unknown_fields_from_the_client(client, saved_entry):
    result = post_entry(client, {**saved_entry, "DPO": "10.1086/719864"})

    assert result.status == falcon.HTTP_BAD_REQUEST


@pytest.mark.parametrize("entry", [{}, {"id": ""}, {"id": None}, {"id": 47}])
def test_update_without_a_usable_id_is_rejected(entry, bibliography, user):
    with pytest.raises(DataError, match="id is required"):
        bibliography.update({**entry, "type": "book"}, user)


def test_update_of_unknown_id_is_not_found(bibliography, user):
    with pytest.raises(NotFoundError):
        bibliography.update({"id": "does-not-exist", "type": "book"}, user)


def test_get_returns_the_server_owned_fields_the_editor_round_trips(
    client, aliased_entry
):
    fetched_entry = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json

    assert fetched_entry["aliases"] == [PARTNER_ALIAS]
    assert fetched_entry["citationKey"] == CITATION_KEY


def test_round_tripped_entry_is_accepted(client, bibliography, aliased_entry):
    fetched_entry = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json

    result = post_entry(client, {**fetched_entry, "title": CORRECTED_TITLE})

    assert result.status == falcon.HTTP_NO_CONTENT
    assert bibliography.find(aliased_entry["id"]) == {
        **fetched_entry,
        "title": CORRECTED_TITLE,
    }


def test_round_tripped_entry_keeps_identity_resolvable(
    client, bibliography, aliased_entry
):
    fetched_entry = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json

    post_entry(client, {**fetched_entry, "title": CORRECTED_TITLE})

    assert bibliography.find(PARTNER_ALIAS["value"])["id"] == aliased_entry["id"]
    assert bibliography.find(CITATION_KEY)["id"] == aliased_entry["id"]


def test_round_tripped_entry_does_not_change_reservations(
    client, database, aliased_entry
):
    fetched_entry = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json
    before = reservations(database)

    post_entry(client, {**fetched_entry, "title": CORRECTED_TITLE})

    assert reservations(database) == before

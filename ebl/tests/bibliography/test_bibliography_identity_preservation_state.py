import falcon
import pytest

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.errors import DataError
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
    reservations,
)


DEPRECATED_ERROR = "RN2001 is deprecated; edit rla_9_388 instead"


def deprecated_payload(deprecated_entry: dict, **overrides) -> dict:
    return {**metadata_only_payload(deprecated_entry), "id": "RN2001", **overrides}


def test_metadata_update_keeps_every_reservation(client, database, aliased_entry):
    before = reservations(database)

    post_entry(client, metadata_only_payload(aliased_entry))

    assert set(reservations(database)) == set(before)
    assert set(before) == {aliased_entry["id"], CITATION_KEY, PARTNER_ALIAS["value"]}


def test_metadata_update_does_not_retire_reservations(client, database, aliased_entry):
    post_entry(client, metadata_only_payload(aliased_entry))

    assert [document["state"] for document in reservations(database).values()] == [
        LookupReservationState.COMMITTED.value
    ] * 3


def test_metadata_update_keeps_reservation_owners(client, database, aliased_entry):
    owners_before = {
        value: document["owner"] for value, document in reservations(database).items()
    }

    post_entry(client, metadata_only_payload(aliased_entry))

    assert {
        value: document["owner"] for value, document in reservations(database).items()
    } == owners_before


def test_rejected_identity_input_adds_no_reservations(client, database, aliased_entry):
    payload = {
        **metadata_only_payload(aliased_entry),
        "citationKey": "brand-new-key",
        "aliases": [{"value": "brand-new", "normalizedValue": "brand-new"}],
    }

    result = post_entry(client, payload)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "brand-new-key" not in reservations(database)
    assert "brand-new" not in reservations(database)


def test_deprecated_record_update_is_rejected(bibliography, user, deprecated_entry):
    with pytest.raises(DataError, match=DEPRECATED_ERROR):
        bibliography.update(deprecated_payload(deprecated_entry), user)


def test_rejected_deprecated_update_keeps_tombstone(
    bibliography, user, database, deprecated_entry
):
    with pytest.raises(DataError, match=DEPRECATED_ERROR):
        bibliography.update(deprecated_payload(deprecated_entry), user)
    stored_entry = database["bibliography"].find_one({"_id": "RN2001"})

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"


def test_rejected_deprecated_update_keeps_redirect_working(
    bibliography, user, deprecated_entry
):
    with pytest.raises(DataError, match=DEPRECATED_ERROR):
        bibliography.update(deprecated_payload(deprecated_entry), user)

    assert bibliography.find("RN2001")["id"] == "rla_9_388"


def test_deprecated_record_update_cannot_clear_tombstone_fields(
    bibliography, user, database, deprecated_entry
):
    with pytest.raises(DataError, match=DEPRECATED_ERROR):
        bibliography.update(
            deprecated_payload(deprecated_entry, deprecated=False), user
        )
    stored_entry = database["bibliography"].find_one({"_id": "RN2001"})

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"

from typing import NoReturn

import pytest

from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.errors import NotFoundError
from ebl.tests.bibliography.lookup_reservation_test_helpers import (
    COLLECTION,
    LATER,
    NOW,
    assert_duplicate_alias_reservation_fails_closed,
    assert_duplicate_citation_key_reservations_are_reconciled,
    assert_expired_pending_reservation_is_committed,
    assert_ttl_deleted_abandoned_reservation_is_reclaimed,
    mongo_datetime,
    operation,
)


def test_reconcile_abandons_expired_pending_reservation(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 1

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value
    assert reservation["deleteAt"] == mongo_datetime(LATER)


def test_reconcile_retains_unexpired_pending_reservation(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    assert bibliography_repository.reconcile_lookup_reservations(NOW) == 0
    assert database[COLLECTION].find_one({"_id": "legacy-id"})["state"] == "pending"


def test_reconcile_commits_expired_pending_reservation_with_entry(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    assert_expired_pending_reservation_is_committed(
        database, bibliography_repository, create_mongo_bibliography_entry
    )


def test_expired_pending_ownership_lookup_not_found_is_not_suppressed(
    monkeypatch, bibliography_repository
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )

    def fail_ownership_lookup(_entry_id: str, _value: str) -> NoReturn:
        raise NotFoundError("ownership lookup failed")

    monkeypatch.setattr(
        bibliography_repository, "_entry_owns_lookup_value", fail_ownership_lookup
    )

    with pytest.raises(NotFoundError, match="ownership lookup failed"):
        bibliography_repository.reconcile_lookup_reservations(LATER)


def test_reconcile_abandons_duplicate_citation_key_reservation_and_keeps_unique_one(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    assert_duplicate_citation_key_reservations_are_reconciled(
        database, bibliography_repository, create_mongo_bibliography_entry
    )


def test_lookup_value_is_reserved_fails_closed_for_duplicate_alias(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    assert_duplicate_alias_reservation_fails_closed(
        database, bibliography_repository, create_mongo_bibliography_entry
    )


def test_reconcile_retires_stale_committed_reservation(
    database, bibliography_repository
):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 1

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value
    assert reservation["deleteAt"] == mongo_datetime(LATER)


def test_lookup_value_is_reserved_repairs_stale_committed_reservation(
    database, bibliography_repository
):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    assert bibliography_repository.lookup_value_is_reserved("legacy-id") is False

    assert database[COLLECTION].find_one({"_id": "legacy-id"})["state"] == "abandoned"


def test_expired_abandoned_reservation_can_be_reclaimed(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )
    bibliography_repository.reconcile_lookup_reservations(LATER)

    bibliography_repository.claim_lookup_values(operation("other"), ["legacy-id"])

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["owner"] == "other"
    assert reservation["state"] == LookupReservationState.PENDING.value


def test_reclaim_survives_abandoned_reservation_ttl_delete(
    monkeypatch, database, bibliography_repository
):
    assert_ttl_deleted_abandoned_reservation_is_reclaimed(
        monkeypatch, database, bibliography_repository
    )


def test_retire_lookup_values_abandons_only_matching_committed_claim(
    database, bibliography_repository
):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["old", "kept"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    bibliography_repository.retire_lookup_values("Q30000000", ["old"], LATER)

    assert database[COLLECTION].find_one({"_id": "old"})["state"] == "abandoned"
    assert database[COLLECTION].find_one({"_id": "kept"})["state"] == "committed"


def test_retire_keeps_a_value_readded_before_finalization(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    current_operation = operation("old-owner")
    bibliography_repository.claim_lookup_values(current_operation, ["readded"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)
    database["bibliography"].insert_one(
        create_mongo_bibliography_entry(
            {
                "id": "Q30000000",
                "type": "book",
                "aliases": [{"value": "readded"}],
            }
        )
    )

    bibliography_repository.retire_lookup_values("Q30000000", ["readded"], LATER)

    reservation = database[COLLECTION].find_one({"_id": "readded"})
    assert reservation is not None
    assert reservation["state"] == LookupReservationState.COMMITTED.value

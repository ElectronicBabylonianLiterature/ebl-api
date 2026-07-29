from datetime import datetime, timedelta

import pytest

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)

COLLECTION = "bibliography_lookup_reservations"
NOW = datetime(2099, 1, 1)
LATER = NOW + timedelta(minutes=10)


def operation(owner: str, entry_id: str = "Q30000000") -> LookupReservationOperation:
    return LookupReservationOperation(owner, entry_id, LATER)


def test_claim_lookup_values_creates_pending_reservation(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    assert database[COLLECTION].find_one({"_id": "legacy-id"}) == {
        "_id": "legacy-id",
        "value": "legacy-id",
        "entryId": "Q30000000",
        "owner": "owner",
        "state": LookupReservationState.PENDING.value,
        "createdAt": database[COLLECTION].find_one({"_id": "legacy-id"})["createdAt"],
        "expiresAt": LATER,
    }


def test_same_operation_reclaim_is_idempotent(database, bibliography_repository):
    current_operation = operation("owner")

    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])

    assert database[COLLECTION].count_documents({"_id": "legacy-id"}) == 1


def test_different_operation_conflicts(database, bibliography_repository):
    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    with pytest.raises(LookupValueReservationError):
        bibliography_repository.claim_lookup_values(operation("other"), ["legacy-id"])


def test_release_is_owner_scoped(database, bibliography_repository):
    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    bibliography_repository.release_pending_lookup_values("other")

    assert database[COLLECTION].count_documents({"_id": "legacy-id"}) == 1


def test_partial_claim_failure_rolls_back_new_values(database, bibliography_repository):
    bibliography_repository.claim_lookup_values(operation("owner"), ["reserved"])

    with pytest.raises(LookupValueReservationError):
        bibliography_repository.claim_lookup_values(
            operation("other"), ["new-value", "reserved"]
        )

    assert database[COLLECTION].find_one({"_id": "new-value"}) is None


def test_commit_lookup_values(database, bibliography_repository):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])

    bibliography_repository.commit_lookup_values(current_operation, NOW)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.COMMITTED.value
    assert reservation["committedAt"] == NOW
    assert "expiresAt" not in reservation


def test_committed_claim_is_not_released_as_pending(database, bibliography_repository):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    bibliography_repository.release_pending_lookup_values("owner")

    assert database[COLLECTION].count_documents({"_id": "legacy-id"}) == 1


def test_reconcile_abandons_expired_pending_reservation(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 1

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value
    assert reservation["deleteAt"] == LATER


def test_reconcile_retains_unexpired_pending_reservation(
    database, bibliography_repository
):
    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    assert bibliography_repository.reconcile_lookup_reservations(NOW) == 0
    assert database[COLLECTION].find_one({"_id": "legacy-id"})["state"] == "pending"


def test_reconcile_commits_expired_pending_reservation_with_entry(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )
    database["bibliography"].insert_one(
        create_mongo_bibliography_entry(
            {"id": "Q30000000", "type": "book", "aliases": [{"value": "legacy-id"}]}
        )
    )

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 1

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.COMMITTED.value
    assert "expiresAt" not in reservation


def test_reconcile_retires_stale_committed_reservation(
    database, bibliography_repository
):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 1

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value
    assert reservation["deleteAt"] == LATER


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


def test_retire_lookup_values_abandons_only_matching_committed_claim(
    database, bibliography_repository
):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["old", "kept"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    bibliography_repository.retire_lookup_values("Q30000000", ["old"], LATER)

    assert database[COLLECTION].find_one({"_id": "old"})["state"] == "abandoned"
    assert database[COLLECTION].find_one({"_id": "kept"})["state"] == "committed"

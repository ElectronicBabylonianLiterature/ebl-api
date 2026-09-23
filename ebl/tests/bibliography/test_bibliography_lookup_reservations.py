import pytest

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationState,
)
from ebl.tests.bibliography.lookup_reservation_test_helpers import (
    COLLECTION,
    LATER,
    NOW,
    mongo_datetime,
    operation,
)


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
        "expiresAt": mongo_datetime(LATER),
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
    assert reservation["committedAt"] == mongo_datetime(NOW)
    assert "expiresAt" not in reservation


def test_committed_claim_is_not_released_as_pending(database, bibliography_repository):
    current_operation = operation("owner")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)

    bibliography_repository.release_pending_lookup_values("owner")

    assert database[COLLECTION].count_documents({"_id": "legacy-id"}) == 1

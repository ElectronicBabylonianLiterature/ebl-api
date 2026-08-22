from datetime import datetime, timedelta, timezone

from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.lookup_reservation_reconciliation import (
    reconcile_reservation,
)

COLLECTION = "bibliography_lookup_reservations"
NOW = datetime(2099, 1, 1, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=10)


def _pending_snapshot(value: str, entry_id: str) -> dict:
    return {
        "_id": value,
        "value": value,
        "entryId": entry_id,
        "owner": "owner",
        "state": LookupReservationState.PENDING.value,
        "createdAt": NOW,
        "expiresAt": NOW,
    }


def _committed_snapshot(value: str, entry_id: str) -> dict:
    return {
        "_id": value,
        "value": value,
        "entryId": entry_id,
        "owner": "owner",
        "state": LookupReservationState.COMMITTED.value,
        "committedAt": NOW,
    }


def test_concurrent_commit_race_on_the_same_stale_candidate_is_idempotent(
    database, bibliography_repository
):
    collection = bibliography_repository._lookup_reservations._collection
    database[COLLECTION].insert_one(_pending_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: True)
    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: True)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.COMMITTED.value


def test_concurrent_abandon_race_from_expired_pending_is_idempotent(
    database, bibliography_repository
):
    collection = bibliography_repository._lookup_reservations._collection
    database[COLLECTION].insert_one(_pending_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: False)
    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: False)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value


def test_concurrent_abandon_race_from_committed_is_idempotent(
    database, bibliography_repository
):
    collection = bibliography_repository._lookup_reservations._collection
    database[COLLECTION].insert_one(_committed_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: False)
    reconcile_reservation(collection, stale_read, LATER, lambda entry_id, value: False)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value


def test_reconciliation_race_does_not_fail_an_unrelated_claim(
    monkeypatch, database, bibliography_repository
):
    """A committed reservation no longer owned by its entry is always a
    reconcile candidate, independent of wall-clock time, so it's used here to
    deterministically simulate a second reconciler winning the abandon race
    on the exact request that also claims an unrelated value.
    """
    database[COLLECTION].insert_one(_committed_snapshot("legacy-id", "Q30000000"))
    collection = bibliography_repository._lookup_reservations._collection
    original_update_one = collection.update_one

    def racing_update_one(query, update):
        if query.get("_id") == "legacy-id" and query.get("state") == "committed":
            database[COLLECTION].update_one(
                {"_id": "legacy-id"},
                {"$set": {"state": "abandoned"}, "$unset": {"expiresAt": ""}},
            )
        return original_update_one(query, update)

    monkeypatch.setattr(collection, "update_one", racing_update_one)

    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("other-owner", "Q30000001", LATER),
        ["unrelated-value"],
    )

    assert (
        database[COLLECTION].find_one({"_id": "unrelated-value"})["state"]
        == LookupReservationState.PENDING.value
    )
    assert (
        database[COLLECTION].find_one({"_id": "legacy-id"})["state"]
        == LookupReservationState.ABANDONED.value
    )

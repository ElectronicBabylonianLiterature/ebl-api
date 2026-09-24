from datetime import datetime, timedelta, timezone

import pytest
from pymongo.database import Database
from pymongo.results import UpdateResult

from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.lookup_reservation_reconciliation import (
    LookupReservationReconciler,
)
from ebl.mongo_collection import MongoCollection

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
    reconciler = LookupReservationReconciler(collection)
    database[COLLECTION].insert_one(_pending_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: True)
    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: True)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.COMMITTED.value


def test_concurrent_abandon_race_from_expired_pending_is_idempotent(
    database, bibliography_repository
):
    collection = bibliography_repository._lookup_reservations._collection
    reconciler = LookupReservationReconciler(collection)
    database[COLLECTION].insert_one(_pending_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: False)
    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: False)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value


def test_concurrent_abandon_race_from_committed_is_idempotent(
    database, bibliography_repository
):
    collection = bibliography_repository._lookup_reservations._collection
    reconciler = LookupReservationReconciler(collection)
    database[COLLECTION].insert_one(_committed_snapshot("legacy-id", "Q30000000"))
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})

    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: False)
    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: False)

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation["state"] == LookupReservationState.ABANDONED.value


def replace_generation_during_update(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    collection: MongoCollection,
    replacement: dict[str, object],
) -> None:
    original_update_one = collection.update_one

    def replace_then_update(
        query: dict[str, object], update: dict[str, object]
    ) -> UpdateResult:
        database[COLLECTION].delete_one({"_id": replacement["_id"]})
        database[COLLECTION].insert_one(replacement)
        return original_update_one(query, update)

    monkeypatch.setattr(collection, "update_one", replace_then_update)


def test_stale_pending_snapshot_does_not_commit_a_replacement_generation(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository,
) -> None:
    collection = bibliography_repository._lookup_reservations._collection
    reconciler = LookupReservationReconciler(collection)
    stale_reservation = _pending_snapshot("legacy-id", "Q30000000")
    replacement = {**stale_reservation, "owner": "replacement-owner"}
    database[COLLECTION].insert_one(stale_reservation)
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert stale_read is not None
    replace_generation_during_update(monkeypatch, database, collection, replacement)

    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: True)

    stored_reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert stored_reservation is not None
    assert stored_reservation["owner"] == "replacement-owner"
    assert stored_reservation["state"] == LookupReservationState.PENDING.value
    assert "committedAt" not in stored_reservation


def test_stale_committed_snapshot_does_not_abandon_a_replacement_generation(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository,
) -> None:
    collection = bibliography_repository._lookup_reservations._collection
    reconciler = LookupReservationReconciler(collection)
    stale_reservation = _committed_snapshot("legacy-id", "Q30000000")
    replacement = {**stale_reservation, "owner": "replacement-owner"}
    database[COLLECTION].insert_one(stale_reservation)
    stale_read = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert stale_read is not None
    replace_generation_during_update(monkeypatch, database, collection, replacement)

    reconciler.reconcile(stale_read, LATER, lambda entry_id, value: False)

    stored_reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert stored_reservation is not None
    assert stored_reservation["owner"] == "replacement-owner"
    assert stored_reservation["state"] == LookupReservationState.COMMITTED.value
    assert "deleteAt" not in stored_reservation


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
    hook_calls = {"count": 0}

    def racing_update_one(query, update):
        if query.get("_id") == "legacy-id" and query.get("state") == "committed":
            hook_calls["count"] += 1
            database[COLLECTION].update_one(
                {"_id": "legacy-id"},
                {"$set": {"state": "abandoned"}, "$unset": {"expiresAt": ""}},
            )
        return original_update_one(query, update)

    monkeypatch.setattr(collection, "update_one", racing_update_one)

    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("other-owner", "Q30000001", LATER),
        ["legacy-id", "unrelated-value"],
    )

    assert hook_calls["count"] == 1
    assert (
        database[COLLECTION].find_one({"_id": "unrelated-value"})["state"]
        == LookupReservationState.PENDING.value
    )
    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation is not None
    assert reservation["owner"] == "other-owner"
    assert reservation["state"] == LookupReservationState.PENDING.value

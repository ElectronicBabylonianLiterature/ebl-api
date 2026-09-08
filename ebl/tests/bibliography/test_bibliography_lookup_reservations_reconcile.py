from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.tests.bibliography.lookup_reservation_test_helpers import (
    COLLECTION,
    LATER,
    NOW,
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


def test_reconcile_abandons_duplicate_citation_key_reservation_and_keeps_unique_one(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner-a", "Q30000000", NOW), ["shared-key"]
    )
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner-b", "Q30000002", NOW), ["unique-key"]
    )
    database["bibliography"].insert_many(
        [
            create_mongo_bibliography_entry(
                {"id": "Q30000000", "type": "book", "citationKey": "shared-key"}
            ),
            create_mongo_bibliography_entry(
                {"id": "Q30000001", "type": "book", "citationKey": "shared-key"}
            ),
            create_mongo_bibliography_entry(
                {"id": "Q30000002", "type": "book", "citationKey": "unique-key"}
            ),
        ]
    )

    assert bibliography_repository.reconcile_lookup_reservations(LATER) == 2

    assert (
        database[COLLECTION].find_one({"_id": "shared-key"})["state"]
        == LookupReservationState.ABANDONED.value
    )
    assert (
        database[COLLECTION].find_one({"_id": "unique-key"})["state"]
        == LookupReservationState.COMMITTED.value
    )


def test_lookup_value_is_reserved_fails_closed_for_duplicate_alias(
    database, bibliography_repository, create_mongo_bibliography_entry
):
    current_operation = operation("owner", entry_id="Q30000000")
    bibliography_repository.claim_lookup_values(current_operation, ["legacy-id"])
    bibliography_repository.commit_lookup_values(current_operation, NOW)
    database["bibliography"].insert_many(
        [
            create_mongo_bibliography_entry(
                {
                    "id": "Q30000000",
                    "type": "book",
                    "aliases": [{"value": "legacy-id", "normalizedValue": "legacy-id"}],
                }
            ),
            create_mongo_bibliography_entry(
                {
                    "id": "Q30000001",
                    "type": "book",
                    "aliases": [{"value": "legacy-id", "normalizedValue": "legacy-id"}],
                }
            ),
        ]
    )

    assert bibliography_repository.lookup_value_is_reserved("legacy-id") is False
    assert (
        database[COLLECTION].find_one({"_id": "legacy-id"})["state"]
        == LookupReservationState.ABANDONED.value
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
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )
    bibliography_repository.reconcile_lookup_reservations(LATER)
    collection = bibliography_repository._lookup_reservations._collection
    original_replace_one = collection.replace_one

    def replace_after_ttl_delete(document, filter_=None, upsert=False):
        database[COLLECTION].delete_one(filter_)
        return original_replace_one(document, filter_, upsert)

    monkeypatch.setattr(collection, "replace_one", replace_after_ttl_delete)

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

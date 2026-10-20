from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest
from pymongo.database import Database

from ebl.bibliography.application.lookup_reservation import LookupReservationOperation
from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository

COLLECTION = "bibliography_lookup_reservations"
NOW = datetime(2099, 1, 1, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=10)
MongoEntryFactory = Callable[[dict[str, object]], dict[str, object]]


def mongo_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


def operation(owner: str, entry_id: str = "Q30000000") -> LookupReservationOperation:
    return LookupReservationOperation(owner, entry_id, LATER)


def assert_expired_pending_reservation_is_committed(
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
    create_mongo_bibliography_entry: MongoEntryFactory,
) -> None:
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
    assert reservation is not None
    assert reservation["state"] == LookupReservationState.COMMITTED.value
    assert "expiresAt" not in reservation


def assert_duplicate_citation_key_reservations_are_reconciled(
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
    create_mongo_bibliography_entry: MongoEntryFactory,
) -> None:
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

    shared_reservation = database[COLLECTION].find_one({"_id": "shared-key"})
    unique_reservation = database[COLLECTION].find_one({"_id": "unique-key"})
    assert shared_reservation is not None
    assert unique_reservation is not None
    assert shared_reservation["state"] == LookupReservationState.ABANDONED.value
    assert unique_reservation["state"] == LookupReservationState.COMMITTED.value


def assert_duplicate_alias_reservation_fails_closed(
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
    create_mongo_bibliography_entry: MongoEntryFactory,
) -> None:
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
    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation is not None
    assert reservation["state"] == LookupReservationState.ABANDONED.value


def assert_ttl_deleted_abandoned_reservation_is_reclaimed(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000000", NOW), ["legacy-id"]
    )
    bibliography_repository.reconcile_lookup_reservations(LATER)
    collection = bibliography_repository._lookup_reservations._collection
    original_replace_one = collection.replace_one

    def replace_after_ttl_delete(
        document: dict[str, object],
        filter_: dict[str, object] | None = None,
        upsert: bool = False,
    ) -> object:
        assert filter_ is not None
        database[COLLECTION].delete_one(filter_)
        return original_replace_one(document, filter_, upsert)

    monkeypatch.setattr(collection, "replace_one", replace_after_ttl_delete)

    bibliography_repository.claim_lookup_values(operation("other"), ["legacy-id"])

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation is not None
    assert reservation["owner"] == "other"
    assert reservation["state"] == LookupReservationState.PENDING.value

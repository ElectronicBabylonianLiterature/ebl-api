import pytest
from pymongo.database import Database
from pymongo.results import UpdateResult

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.errors import DuplicateError
from ebl.tests.bibliography.lookup_reservation_test_helpers import (
    COLLECTION,
    LATER,
    NOW,
    operation,
)


def abandon_reservation(
    bibliography_repository: MongoBibliographyRepository, value: str
) -> None:
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("previous-owner", "Q30000000", NOW), [value]
    )
    bibliography_repository.reconcile_lookup_reservations(LATER)


def test_claim_retries_when_a_reported_insert_is_missing_on_readback(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    collection = bibliography_repository._lookup_reservations._collection
    original_insert_one = collection.insert_one
    insert_calls = {"count": 0}

    def insert_with_missing_first_result(document: dict[str, object]) -> object:
        insert_calls["count"] += 1
        if insert_calls["count"] == 1:
            return document["_id"]
        return original_insert_one(document)

    monkeypatch.setattr(collection, "insert_one", insert_with_missing_first_result)

    bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert insert_calls["count"] == 2
    assert reservation is not None
    assert reservation["owner"] == "owner"
    assert reservation["state"] == LookupReservationState.PENDING.value


def test_claim_fails_closed_when_reported_inserts_keep_disappearing(
    monkeypatch: pytest.MonkeyPatch,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    collection = bibliography_repository._lookup_reservations._collection
    insert_calls = {"count": 0}

    def missing_insert(document: dict[str, object]) -> object:
        insert_calls["count"] += 1
        return document["_id"]

    monkeypatch.setattr(collection, "insert_one", missing_insert)

    with pytest.raises(LookupValueReservationError):
        bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    assert insert_calls["count"] == 2


def test_claim_retries_are_bounded_when_duplicate_rows_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    collection = bibliography_repository._lookup_reservations._collection
    insert_calls = {"count": 0}

    def duplicate_without_row(document: dict[str, object]) -> object:
        insert_calls["count"] += 1
        raise DuplicateError(f"Reservation {document['_id']} disappeared.")

    monkeypatch.setattr(collection, "insert_one", duplicate_without_row)

    with pytest.raises(LookupValueReservationError):
        bibliography_repository.claim_lookup_values(operation("owner"), ["legacy-id"])

    assert insert_calls["count"] == 2


def test_claim_retries_when_ttl_deletes_before_the_post_reconcile_read(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    abandon_reservation(bibliography_repository, "legacy-id")
    collection = bibliography_repository._lookup_reservations._collection
    original_find_one_by_id = collection.find_one_by_id
    find_calls = {"count": 0}

    def find_after_ttl_delete(id_: object) -> object:
        find_calls["count"] += 1
        if find_calls["count"] == 2:
            database[COLLECTION].delete_one({"_id": id_})
        return original_find_one_by_id(id_)

    monkeypatch.setattr(collection, "find_one_by_id", find_after_ttl_delete)

    bibliography_repository.claim_lookup_values(
        operation("new-owner", entry_id="Q30000001"), ["legacy-id"]
    )

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation is not None
    assert reservation["owner"] == "new-owner"
    assert reservation["entryId"] == "Q30000001"


def test_concurrent_abandoned_reclaim_fails_closed_for_the_loser(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    abandon_reservation(bibliography_repository, "legacy-id")
    collection = bibliography_repository._lookup_reservations._collection
    original_replace_one = collection.replace_one

    def replace_after_competing_claim(
        document: dict[str, object],
        filter_: dict[str, object] | None = None,
        upsert: bool = False,
    ) -> UpdateResult:
        assert filter_ is not None
        winning_document = {
            **document,
            "entryId": "Q30000001",
            "owner": "winning-owner",
        }
        result = database[COLLECTION].replace_one(filter_, winning_document)
        assert result.matched_count == 1
        return original_replace_one(document, filter_, upsert)

    monkeypatch.setattr(collection, "replace_one", replace_after_competing_claim)

    with pytest.raises(LookupValueReservationError):
        bibliography_repository.claim_lookup_values(
            operation("losing-owner", entry_id="Q30000002"), ["legacy-id"]
        )

    reservation = database[COLLECTION].find_one({"_id": "legacy-id"})
    assert reservation is not None
    assert reservation["owner"] == "winning-owner"
    assert reservation["entryId"] == "Q30000001"
    assert reservation["state"] == LookupReservationState.PENDING.value

from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence

import pymongo
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.lookup_reservation_reconciliation import (
    LookupReservationReconciler,
)
from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography_lookup_reservations"


@dataclass(frozen=True)
class LookupReservationClaim:
    operation: LookupReservationOperation
    value: str
    now: datetime


class MongoLookupReservations:
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)
        self._reconciler = LookupReservationReconciler(self._collection)

    def create_indexes(self) -> None:
        self._collection.create_index(
            [("value", pymongo.ASCENDING)],
            unique=True,
            name="bibliography_lookup_value_unique",
        )
        self._collection.create_index([("owner", pymongo.ASCENDING)])
        self._collection.create_index([("entryId", pymongo.ASCENDING)])
        self._collection.create_index(
            [("state", pymongo.ASCENDING), ("expiresAt", pymongo.ASCENDING)]
        )
        self._collection.create_index(
            [("deleteAt", pymongo.ASCENDING)], expireAfterSeconds=0
        )

    def claim(
        self,
        operation: LookupReservationOperation,
        values: Sequence[str],
        now: datetime,
        owns_value: Callable[[str, str], bool],
    ) -> None:
        claimed: list[str] = []
        for value in dict.fromkeys(values):
            claim = LookupReservationClaim(operation, value, now)
            try:
                self._insert_pending(claim, owns_value)
            except LookupValueReservationError:
                self._release_values(operation.owner, claimed)
                raise
            claimed.append(value)

    def commit(self, operation: LookupReservationOperation, now: datetime) -> None:
        self._collection.update_many(
            {
                "owner": operation.owner,
                "entryId": operation.entry_id,
                "state": LookupReservationState.PENDING.value,
            },
            {
                "$set": {
                    "state": LookupReservationState.COMMITTED.value,
                    "committedAt": now,
                },
                "$unset": {"expiresAt": "", "deleteAt": ""},
            },
        )

    def release_pending(self, owner: str) -> None:
        with suppress(NotFoundError):
            self._collection.delete_many(
                {"owner": owner, "state": LookupReservationState.PENDING.value}
            )

    def retire(self, entry_id: str, values: Sequence[str], now: datetime) -> None:
        for value in dict.fromkeys(values):
            with suppress(NotFoundError):
                self._reconciler.abandon_value(
                    value, now, entry_id, LookupReservationState.COMMITTED
                )

    def is_active(
        self, value: str, now: datetime, owns_value: Callable[[str, str], bool]
    ) -> bool:
        self.reconcile_value(value, now, owns_value)
        try:
            reservation = self._collection.find_one_by_id(value)
        except NotFoundError:
            return False
        return reservation.get("state") != LookupReservationState.ABANDONED.value

    def reconcile(
        self, now: datetime, owns_value: Callable[[str, str], bool], limit: int
    ) -> int:
        candidates = list(
            self._collection.find_many(
                {
                    "$or": [
                        {
                            "state": LookupReservationState.PENDING.value,
                            "expiresAt": {"$lte": now},
                        },
                        {"state": LookupReservationState.COMMITTED.value},
                    ]
                }
            ).limit(limit)
        )
        for reservation in candidates:
            self._reconciler.reconcile(reservation, now, owns_value)
        return len(candidates)

    def reconcile_value(
        self, value: str, now: datetime, owns_value: Callable[[str, str], bool]
    ) -> None:
        try:
            reservation = self._collection.find_one_by_id(value)
        except NotFoundError:
            return
        self._reconciler.reconcile(reservation, now, owns_value)

    def _insert_pending(
        self,
        claim: LookupReservationClaim,
        owns_value: Callable[[str, str], bool],
    ) -> None:
        last_error: DuplicateError | None = None
        for _ in range(2):
            try:
                self._collection.insert_one(self._pending_document(claim))
            except DuplicateError as error:
                last_error = error
            else:
                try:
                    reservation = self._collection.find_one_by_id(claim.value)
                except NotFoundError:
                    last_error = DuplicateError(
                        f"Lookup reservation {claim.value} disappeared after insertion."
                    )
                    continue
                if self._is_pending_claim(reservation, claim):
                    return
                last_error = DuplicateError(
                    f"Lookup reservation {claim.value} changed during insertion."
                )
            assert last_error is not None
            if self._handle_existing_reservation(claim, owns_value, last_error):
                return
        assert last_error is not None
        raise LookupValueReservationError(claim.value) from last_error

    def _handle_existing_reservation(
        self,
        claim: LookupReservationClaim,
        owns_value: Callable[[str, str], bool],
        error: DuplicateError,
    ) -> bool:
        operation = claim.operation
        value = claim.value
        try:
            reservation = self._collection.find_one_by_id(value)
        except NotFoundError:
            return False
        if (
            reservation.get("owner") == operation.owner
            and reservation.get("entryId") == operation.entry_id
            and reservation.get("state") == LookupReservationState.PENDING.value
        ):
            return True
        if (
            reservation.get("entryId") == operation.entry_id
            and reservation.get("state") == LookupReservationState.COMMITTED.value
            and owns_value(operation.entry_id, value)
        ):
            return True
        self._reconciler.reconcile(reservation, claim.now, owns_value)
        try:
            reservation = self._collection.find_one_by_id(value)
        except NotFoundError:
            return False
        if reservation.get("state") == LookupReservationState.ABANDONED.value:
            try:
                self._collection.replace_one(
                    self._pending_document(claim),
                    {"_id": value, "state": LookupReservationState.ABANDONED.value},
                    upsert=True,
                )
            except DuplicateKeyError as concurrent_error:
                raise LookupValueReservationError(value) from concurrent_error
            return True
        raise LookupValueReservationError(value) from error

    @staticmethod
    def _is_pending_claim(reservation: dict, claim: LookupReservationClaim) -> bool:
        return (
            reservation.get("owner") == claim.operation.owner
            and reservation.get("entryId") == claim.operation.entry_id
            and reservation.get("state") == LookupReservationState.PENDING.value
        )

    def _pending_document(self, claim: LookupReservationClaim) -> dict:
        return {
            "_id": claim.value,
            "value": claim.value,
            "entryId": claim.operation.entry_id,
            "owner": claim.operation.owner,
            "state": LookupReservationState.PENDING.value,
            "createdAt": claim.now,
            "expiresAt": claim.operation.expires_at,
        }

    def _release_values(self, owner: str, values: Sequence[str]) -> None:
        for value in values:
            with suppress(NotFoundError):
                self._collection.delete_one(
                    {
                        "_id": value,
                        "owner": owner,
                        "state": LookupReservationState.PENDING.value,
                    }
                )

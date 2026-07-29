from contextlib import suppress
from datetime import datetime
from typing import Callable, Sequence

import pymongo

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography_lookup_reservations"


class MongoLookupReservations:
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

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
            try:
                self._insert_pending(operation, value, now, owns_value)
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
                self._abandon_value(
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
            self._reconcile_reservation(reservation, now, owns_value)
        return len(candidates)

    def reconcile_value(
        self, value: str, now: datetime, owns_value: Callable[[str, str], bool]
    ) -> None:
        try:
            reservation = self._collection.find_one_by_id(value)
        except NotFoundError:
            return
        self._reconcile_reservation(reservation, now, owns_value)

    def _insert_pending(
        self,
        operation: LookupReservationOperation,
        value: str,
        now: datetime,
        owns_value: Callable[[str, str], bool],
    ) -> None:
        try:
            self._collection.insert_one(self._pending_document(operation, value))
        except DuplicateError as error:
            self._handle_existing_reservation(operation, value, now, owns_value, error)

    def _handle_existing_reservation(
        self,
        operation: LookupReservationOperation,
        value: str,
        now: datetime,
        owns_value: Callable[[str, str], bool],
        error: DuplicateError,
    ) -> None:
        reservation = self._collection.find_one_by_id(value)
        if (
            reservation.get("owner") == operation.owner
            and reservation.get("state") == LookupReservationState.PENDING.value
        ):
            return
        if (
            reservation.get("entryId") == operation.entry_id
            and reservation.get("state") == LookupReservationState.COMMITTED.value
            and owns_value(operation.entry_id, value)
        ):
            return
        self._reconcile_reservation(reservation, now, owns_value)
        reservation = self._collection.find_one_by_id(value)
        if reservation.get("state") == LookupReservationState.ABANDONED.value:
            self._collection.replace_one(
                self._pending_document(operation, value),
                {"_id": value, "state": LookupReservationState.ABANDONED.value},
            )
            return
        raise LookupValueReservationError(value) from error

    def _pending_document(
        self, operation: LookupReservationOperation, value: str
    ) -> dict:
        return {
            "_id": value,
            "value": value,
            "entryId": operation.entry_id,
            "owner": operation.owner,
            "state": LookupReservationState.PENDING.value,
            "createdAt": datetime.utcnow(),
            "expiresAt": operation.expires_at,
        }

    def _reconcile_reservation(
        self, reservation: dict, now: datetime, owns_value: Callable[[str, str], bool]
    ) -> None:
        value = reservation["_id"]
        entry_id = reservation["entryId"]
        state = LookupReservationState(reservation["state"])
        expires_at = reservation.get("expiresAt")
        if (
            state == LookupReservationState.PENDING
            and isinstance(expires_at, datetime)
            and expires_at <= now
        ):
            if owns_value(entry_id, value):
                self._commit_value(value, now)
            else:
                self._abandon_value(value, now, entry_id, state)
        elif state == LookupReservationState.COMMITTED and not owns_value(
            entry_id, value
        ):
            self._abandon_value(value, now, entry_id, state)

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

    def _commit_value(self, value: str, now: datetime) -> None:
        self._collection.update_one(
            {"_id": value, "state": LookupReservationState.PENDING.value},
            {
                "$set": {
                    "state": LookupReservationState.COMMITTED.value,
                    "committedAt": now,
                },
                "$unset": {"expiresAt": "", "deleteAt": ""},
            },
        )

    def _abandon_value(
        self,
        value: str,
        now: datetime,
        entry_id: str,
        state: LookupReservationState,
    ) -> None:
        self._collection.update_one(
            {"_id": value, "entryId": entry_id, "state": state.value},
            {
                "$set": {
                    "state": LookupReservationState.ABANDONED.value,
                    "deleteAt": now,
                },
                "$unset": {"expiresAt": ""},
            },
        )

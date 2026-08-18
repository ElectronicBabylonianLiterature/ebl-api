from datetime import datetime, timezone
from typing import Callable

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.mongo_collection import MongoCollection


def to_utc_datetime(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


class LookupReservationReconciler:
    def __init__(self, collection: MongoCollection) -> None:
        self._collection = collection

    def reconcile(
        self, reservation: dict, now: datetime, owns_value: Callable[[str, str], bool]
    ) -> None:
        value = reservation["_id"]
        entry_id = reservation["entryId"]
        state = LookupReservationState(reservation["state"])
        expires_at = reservation.get("expiresAt")
        comparison_now = to_utc_datetime(now)
        if self._is_expired_pending(state, expires_at, comparison_now):
            if owns_value(entry_id, value):
                self.commit_value(value, comparison_now)
            else:
                self.abandon_value(value, comparison_now, entry_id, state)
        elif state == LookupReservationState.COMMITTED and not owns_value(
            entry_id, value
        ):
            self.abandon_value(value, comparison_now, entry_id, state)

    def _is_expired_pending(
        self,
        state: LookupReservationState,
        expires_at: object,
        comparison_now: datetime,
    ) -> bool:
        return (
            state == LookupReservationState.PENDING
            and isinstance(expires_at, datetime)
            and to_utc_datetime(expires_at) <= comparison_now
        )

    def commit_value(self, value: str, now: datetime) -> None:
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

    def abandon_value(
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

from contextlib import suppress
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.errors import NotFoundError
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
        self,
        reservation: Dict[str, Any],
        now: datetime,
        owns_value: Callable[[str, str], bool],
    ) -> None:
        value = reservation["_id"]
        entry_id = reservation["entryId"]
        state = LookupReservationState(reservation["state"])
        expires_at = reservation.get("expiresAt")
        comparison_now = to_utc_datetime(now)
        if self._is_expired_pending(state, expires_at, comparison_now):
            is_owner = owns_value(entry_id, value)
            with suppress(NotFoundError):
                if is_owner:
                    self._commit_value(reservation, comparison_now)
                else:
                    self._abandon_reservation(reservation, comparison_now)
        elif state == LookupReservationState.COMMITTED and not owns_value(
            entry_id, value
        ):
            with suppress(NotFoundError):
                self._abandon_reservation(reservation, comparison_now)

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

    def _commit_value(self, reservation: Dict[str, Any], now: datetime) -> None:
        self._collection.update_one(
            self._snapshot_filter(reservation),
            {
                "$set": {
                    "state": LookupReservationState.COMMITTED.value,
                    "committedAt": now,
                },
                "$unset": {"expiresAt": "", "deleteAt": ""},
            },
        )

    def _abandon_reservation(self, reservation: Dict[str, Any], now: datetime) -> None:
        self._collection.update_one(
            self._snapshot_filter(reservation),
            {
                "$set": {
                    "state": LookupReservationState.ABANDONED.value,
                    "deleteAt": now,
                },
                "$unset": {"expiresAt": ""},
            },
        )

    @staticmethod
    def _snapshot_filter(reservation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            field: reservation[field] for field in ("_id", "entryId", "owner", "state")
        }

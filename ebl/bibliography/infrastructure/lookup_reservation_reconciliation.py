from contextlib import suppress
from datetime import datetime, timezone
from typing import Callable

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection


def _to_utc_datetime(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


def reconcile_reservation(
    collection: MongoCollection,
    reservation: dict,
    now: datetime,
    owns_value: Callable[[str, str], bool],
) -> None:
    """Advance a stale/committed reservation candidate to its next state.

    A concurrent reconciler may have already advanced the same candidate
    between the read that produced `reservation` and this write, so the
    conditional update below can legitimately match zero documents -- that
    means the transition already happened, not that anything failed.
    Suppressed the same way `retire`/`release_pending` already suppress it
    for their own no-longer-matching updates.
    """
    value = reservation["_id"]
    entry_id = reservation["entryId"]
    state = LookupReservationState(reservation["state"])
    expires_at = reservation.get("expiresAt")
    comparison_now = _to_utc_datetime(now)
    if (
        state == LookupReservationState.PENDING
        and isinstance(expires_at, datetime)
        and _to_utc_datetime(expires_at) <= comparison_now
    ):
        with suppress(NotFoundError):
            if owns_value(entry_id, value):
                commit_value(collection, value, comparison_now)
            else:
                abandon_value(collection, value, comparison_now, entry_id, state)
    elif state == LookupReservationState.COMMITTED and not owns_value(
        entry_id, value
    ):
        with suppress(NotFoundError):
            abandon_value(collection, value, comparison_now, entry_id, state)


def commit_value(collection: MongoCollection, value: str, now: datetime) -> None:
    collection.update_one(
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
    collection: MongoCollection,
    value: str,
    now: datetime,
    entry_id: str,
    state: LookupReservationState,
) -> None:
    collection.update_one(
        {"_id": value, "entryId": entry_id, "state": state.value},
        {
            "$set": {
                "state": LookupReservationState.ABANDONED.value,
                "deleteAt": now,
            },
            "$unset": {"expiresAt": ""},
        },
    )

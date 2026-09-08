from datetime import datetime, timedelta, timezone

from ebl.bibliography.application.lookup_reservation import LookupReservationOperation

COLLECTION = "bibliography_lookup_reservations"
NOW = datetime(2099, 1, 1, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=10)


def mongo_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


def operation(owner: str, entry_id: str = "Q30000000") -> LookupReservationOperation:
    return LookupReservationOperation(owner, entry_id, LATER)

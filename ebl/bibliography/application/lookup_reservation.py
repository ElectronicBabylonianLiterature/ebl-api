from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

PENDING_RESERVATION_LIFETIME = timedelta(hours=1)


class LookupReservationState(str, Enum):
    PENDING = "pending"
    COMMITTED = "committed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class LookupReservationOperation:
    owner: str
    entry_id: str
    expires_at: datetime


def new_lookup_reservation_operation(
    entry_id: str, now: datetime
) -> LookupReservationOperation:
    return LookupReservationOperation(
        owner=uuid4().hex,
        entry_id=entry_id,
        expires_at=now + PENDING_RESERVATION_LIFETIME,
    )

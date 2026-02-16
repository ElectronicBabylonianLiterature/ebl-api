import datetime
from enum import Enum
from typing import Sequence

import attr

from ebl.users.domain.user import User


def now() -> str:
    return datetime.datetime.utcnow().isoformat()


class RecordType(Enum):
    TRANSLITERATION = "Transliteration"
    REVISION = "Revision"
    HISTORICAL_TRANSLITERATION = "HistoricalTransliteration"
    COLLATION = "Collation"


@attr.s(auto_attribs=True, frozen=True)
class RecordEntry:
    user: str
    type: RecordType
    date: str = attr.ib(factory=now)

    @staticmethod
    def transliteration(user: str) -> "RecordEntry":
        return RecordEntry(user, RecordType.TRANSLITERATION)

    @staticmethod
    def revision(user: str) -> "RecordEntry":
        return RecordEntry(user, RecordType.REVISION)


@attr.s(auto_attribs=True, frozen=True)
class Record:
    entries: Sequence[RecordEntry] = ()

    def add_entry(
        self, old_transliteration: str, new_transliteration: str, user: User
    ) -> "Record":
        if new_transliteration != old_transliteration:
            return Record(
                (*self.entries, self._create_entry(old_transliteration, user.ebl_name))
            )
        else:
            return self

    @staticmethod
    def _create_entry(old_transliteration: str, user: str) -> RecordEntry:
        return (
            RecordEntry.revision(user)
            if old_transliteration
            else RecordEntry.transliteration(user)
        )

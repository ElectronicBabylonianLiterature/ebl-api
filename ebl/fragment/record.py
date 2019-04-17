# pylint: disable=R0903
import datetime
from enum import Enum
from typing import Dict, List, Tuple

import attr


class RecordType(Enum):
    TRANSLITERATION = 'Transliteration'
    REVISION = 'Revision'
    HISTORICAL_TRANSLITERATION = 'HistoricalTransliteration'
    COLLATION = 'Collation'


@attr.s(auto_attribs=True, frozen=True)
class RecordEntry:
    user: str
    type: RecordType
    date: str

    def to_dict(self) -> Dict[str, str]:
        return {
            'user': self.user,
            'type': self.type.value,
            'date': self.date
        }


@attr.s(auto_attribs=True, frozen=True)
class Record:
    entries: Tuple[RecordEntry, ...] = tuple()

    def add_entry(self,
                  old_transliteration: str,
                  new_transliteration: str,
                  user) -> 'Record':
        if new_transliteration != old_transliteration:
            return Record((
                *self.entries,
                self._create_entry(old_transliteration, user)
            ))
        else:
            return self

    def to_list(self) -> List[Dict[str, str]]:
        return [entry.to_dict() for entry in self.entries]

    @staticmethod
    def _create_entry(old_transliteration: str, user) -> RecordEntry:
        record_type = (
            RecordType.REVISION
            if old_transliteration
            else RecordType.TRANSLITERATION
        )
        return RecordEntry(
            user.ebl_name,
            record_type,
            datetime.datetime.utcnow().isoformat()
        )

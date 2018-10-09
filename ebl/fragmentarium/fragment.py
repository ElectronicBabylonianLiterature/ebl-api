import copy
import datetime

TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class Fragment:

    def __init__(self, data):
        self._data = copy.deepcopy(data)

    def update_transliteration(self, transliteration, notes, user):
        record = Record(self._data['record']).add_entry(
            self._data['transliteration'],
            transliteration,
            user
        )

        return Fragment({
            **self._data,
            'transliteration': transliteration,
            'notes': notes,
            'record': record.entries
        })

    def to_dict(self):
        return copy.deepcopy(self._data)


class Record:

    def __init__(self, record):
        self._entries = copy.deepcopy(record)

    @property
    def entries(self):
        return copy.deepcopy(self._entries)

    def add_entry(self, old_transliteration, new_transliteration, user):
        if new_transliteration != old_transliteration:
            return Record([
                *self._entries,
                self._create_entry(old_transliteration, user)
            ])
        else:
            return self

    @staticmethod
    def _create_entry(old_transliteration, user):
        record_type = REVISION if old_transliteration else TRANSLITERATION
        return {
            'user': user.ebl_name,
            'type': record_type,
            'date': datetime.datetime.utcnow().isoformat()
        }

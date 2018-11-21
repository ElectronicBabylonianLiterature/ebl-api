import copy
import datetime
import json
import pydash
from ebl.fragmentarium.lemmatization import Lemmatization
from ebl.fragmentarium.transliteration import Transliteration


TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class Fragment:

    def __init__(self, data):
        self._data = copy.deepcopy(data)

    def __eq__(self, other):
        return isinstance(other, Fragment) and (self._data == other.to_dict())

    def __hash__(self):
        return hash(json.dumps(self._data))

    @property
    def number(self):
        return self._data['_id']

    @property
    def accession(self):
        return self._data['accession']

    @property
    def cdli_number(self):
        return self._data['cdliNumber']

    @property
    def transliteration(self):
        return Transliteration(
            self._data['transliteration'],
            self._data['notes'],
            self._data.get('signs', None)
        )

    @property
    def record(self):
        return Record(self._data['record'])

    @property
    def folios(self):
        return Folios(self._data['folios'])

    @property
    def lemmatization(self):
        return Lemmatization(self._data['lemmatization'])

    def update_transliteration(self, transliteration, user):
        record = Record(self._data['record']).add_entry(
            self.transliteration.atf,
            transliteration.atf,
            user
        )
        lemmatization = (
            Lemmatization.of_transliteration(transliteration).tokens
            if self.transliteration.atf != transliteration.atf
            else self._data.get('lemmatization')
        )

        return Fragment(pydash.omit_by({
            **self._data,
            'transliteration': transliteration.atf,
            'lemmatization': lemmatization,
            'notes': transliteration.notes,
            'signs': transliteration.signs,
            'record': record.entries
        }, lambda value: value is None))

    def add_matching_lines(self, query):
        matching_lines = query.get_matching_lines(self.transliteration)
        return Fragment({
            **self._data,
            'matching_lines': matching_lines
        })

    def update_lemmatization(self, lemmatization):
        return Fragment({
            **self._data,
            'lemmatization': lemmatization.tokens
        })

    def to_dict(self):
        return copy.deepcopy(self._data)

    def to_dict_for(self, user):
        return {
            **self.to_dict(),
            'folios': self.folios.filter(user).entries
        }


class Record:

    def __init__(self, record):
        self._entries = copy.deepcopy(record)

    def __eq__(self, other):
        return isinstance(other, Record) and (self.entries == other.entries)

    def __hash__(self):
        return hash(json.dumps(self._entries))

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


class Folios:

    def __init__(self, folios):
        self._entries = copy.deepcopy(folios)

    def __eq__(self, other):
        return isinstance(other, Folios) and (self.entries == other.entries)

    def __hash__(self):
        return hash(json.dumps(self._entries))

    @property
    def entries(self):
        return copy.deepcopy(self._entries)

    def filter(self, user):
        folios = [
            folio
            for folio in self._entries
            if user.can_read_folio(folio['name'])
        ]
        return Folios(folios)

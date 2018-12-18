import copy
import datetime
import json
import pydash
from ebl.fragmentarium.lemmatization import Lemmatization, LemmatizationError
from ebl.fragmentarium.transliteration import Transliteration


TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


class Fragment:
    # pylint: disable=R0904
    def __init__(self, data):
        self._data = copy.deepcopy(data)

    def __eq__(self, other):
        return isinstance(other, Fragment) and (self._data == other.to_dict())

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
    def bm_id_number(self):
        return self._data['bmIdNumber']

    @property
    def publication(self):
        return self._data['publication']

    @property
    def description(self):
        return self._data['description']

    @property
    def collection(self):
        return self._data['collection']

    @property
    def script(self):
        return self._data['script']

    @property
    def museum(self):
        return self._data['museum']

    @property
    def width(self):
        return {**self._data['width']}

    @property
    def length(self):
        return {**self._data['length']}

    @property
    def thickness(self):
        return {**self._data['thickness']}

    @property
    def joins(self):
        return [*self._data['joins']]

    @property
    def transliteration(self):
        return Transliteration(
            self.lemmatization.atf,
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

    @property
    def hits(self):
        return self._data.get('hits')

    def update_transliteration(self, transliteration, user):
        record = Record(self._data['record']).add_entry(
            self.lemmatization.atf,
            transliteration.atf,
            user
        )
        lemmatization = self.lemmatization.merge(transliteration)

        return Fragment.from_dict(pydash.omit_by({
            **self._data,
            'lemmatization': lemmatization.tokens,
            'notes': transliteration.notes,
            'signs': transliteration.signs,
            'record': record.entries
        }, lambda value: value is None))

    def add_matching_lines(self, query):
        matching_lines = query.get_matching_lines(self.transliteration)
        return Fragment.from_dict({
            **self._data,
            'matching_lines': matching_lines
        })

    def update_lemmatization(self, lemmatization):
        if self.lemmatization.is_compatible(lemmatization):
            return Fragment.from_dict({
                **self._data,
                'lemmatization': lemmatization.tokens
            })
        else:
            raise LemmatizationError()

    def to_dict(self):
        return pydash.omit_by({
            '_id': self.number,
            'accession': self.accession,
            'cdliNumber': self.cdli_number,
            'bmIdNumber': self.bm_id_number,
            'publication': self.publication,
            'description': self.description,
            'joins': self.joins,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'collection': self.collection,
            'script': self.script,
            'notes': self.transliteration.notes,
            'museum': self.museum,
            'signs': self.transliteration.signs,
            'record': self.record.entries,
            'folios': self.folios.entries,
            'lemmatization': self.lemmatization.tokens,
            'hits': self._data.get('hits'),
            'matching_lines': self._data.get('matching_lines')
        }, lambda value: value is None)

    def to_dict_for(self, user):
        return {
            **self.to_dict(),
            'folios': self.folios.filter(user).entries
        }

    @staticmethod
    def from_dict(data):
        return Fragment(data)


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

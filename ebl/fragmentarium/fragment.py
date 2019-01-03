# pylint: disable=R0903
import datetime
from typing import Tuple, Optional
import attr
import pydash
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.text.atf import AtfSyntaxError
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text
from ebl.fragmentarium.transliteration import (
    Transliteration, TransliterationError
)

TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return attr.asdict(self, filter=lambda _, value: value is not None)


@attr.s(auto_attribs=True, frozen=True)
class RecordEntry:
    user: str
    type: str
    date: str

    def to_dict(self) -> dict:
        return attr.asdict(self)


@attr.s(auto_attribs=True, frozen=True)
class Record:
    entries: Tuple[RecordEntry, ...] = tuple()

    def add_entry(self,
                  old_transliteration: str,
                  new_transliteration: str, user) -> 'Record':
        if new_transliteration != old_transliteration:
            return Record((
                *self.entries,
                self._create_entry(old_transliteration, user)
            ))
        else:
            return self

    def to_list(self) -> list:
        return [entry.to_dict() for entry in self.entries]

    @staticmethod
    def _create_entry(old_transliteration: str, user) -> RecordEntry:
        record_type = REVISION if old_transliteration else TRANSLITERATION
        return RecordEntry(
            user.ebl_name,
            record_type,
            datetime.datetime.utcnow().isoformat()
        )


@attr.s(auto_attribs=True, frozen=True)
class Folio:
    name: str
    number: str

    def to_dict(self) -> dict:
        return attr.asdict(self)


@attr.s(auto_attribs=True, frozen=True)
class Folios:
    entries: Tuple[Folio, ...] = tuple()

    def filter(self, user) -> 'Folios':
        folios = tuple(
            folio
            for folio in self.entries
            if user.can_read_folio(folio.name)
        )
        return Folios(folios)

    def to_list(self) -> list:
        return [folio.to_dict() for folio in self.entries]


@attr.s(auto_attribs=True, frozen=True)
class Fragment:
    number: str
    accession: str = ''
    cdli_number: str = ''
    bm_id_number: str = ''
    publication: str = ''
    description: str = ''
    collection: str = ''
    script: str = ''
    museum: str = ''
    width: Measure = Measure()
    length: Measure = Measure()
    thickness: Measure = Measure()
    joins: Tuple[str, ...] = tuple()
    record: Record = Record()
    folios: Folios = Folios()
    lemmatization: Lemmatization = Lemmatization()
    text: Text = Text()
    signs: Optional[str] = None
    notes: str = ''
    hits: Optional[int] = None
    matching_lines: Optional[tuple] = None

    @property
    def transliteration(self) -> Transliteration:
        return Transliteration(
            self.lemmatization.atf,
            self.notes,
            self.signs
        )

    def update_transliteration(self, transliteration, user) -> 'Fragment':
        record = self.record.add_entry(
            self.lemmatization.atf,
            transliteration.atf,
            user
        )
        lemmatization = self.lemmatization.merge(transliteration)

        try:
            text = parse_atf(transliteration.atf)

            return attr.evolve(
                self,
                lemmatization=lemmatization,
                text=text,
                notes=transliteration.notes,
                signs=transliteration.signs,
                record=record
            )
        except AtfSyntaxError as error:
            errors = [{
                'description': 'Invalid line',
                'lineNumber': error.line_number
            }]
            raise TransliterationError(errors)

    def add_matching_lines(self, query) -> 'Fragment':
        matching_lines = query.get_matching_lines(self.transliteration)
        return attr.evolve(
            self,
            matching_lines=matching_lines
        )

    def update_lemmatization(self, lemmatization: Lemmatization) -> 'Fragment':
        old_lemmatization = self.text.lemmatization
        if old_lemmatization.is_compatible(lemmatization):
            return attr.evolve(
                self,
                lemmatization=lemmatization
            )
        else:
            raise LemmatizationError()

    def to_dict(self) -> dict:
        return pydash.omit_by({
            '_id': self.number,
            'accession': self.accession,
            'cdliNumber': self.cdli_number,
            'bmIdNumber': self.bm_id_number,
            'publication': self.publication,
            'description': self.description,
            'joins': list(self.joins),
            'length': self.length.to_dict(),
            'width': self.width.to_dict(),
            'thickness': self.thickness.to_dict(),
            'collection': self.collection,
            'script': self.script,
            'notes': self.notes,
            'museum': self.museum,
            'signs': self.signs,
            'record': self.record.to_list(),
            'folios': self.folios.to_list(),
            'lemmatization': self.lemmatization.to_list(),
            'text': self.text.to_dict(),
            'hits': self.hits,
            'matching_lines': self.matching_lines
        }, lambda value: value is None)

    def to_dict_for(self, user) -> dict:
        return {
            **self.to_dict(),
            'folios': self.folios.filter(user).to_list()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Fragment':
        return Fragment(
            data['_id'],
            data['accession'],
            data['cdliNumber'],
            data['bmIdNumber'],
            data['publication'],
            data['description'],
            data['collection'],
            data['script'],
            data['museum'],
            Measure(**data['width']),
            Measure(**data['length']),
            Measure(**data['thickness']),
            tuple(data['joins']),
            Record(tuple(RecordEntry(**entry) for entry in data['record'])),
            Folios(tuple(Folio(**folio) for folio in data['folios'])),
            Lemmatization.from_list(data['lemmatization']),
            Text.from_dict(data['text']),
            data.get('signs'),
            data['notes'],
            data.get('hits'),
            data.get('matching_lines')
        )

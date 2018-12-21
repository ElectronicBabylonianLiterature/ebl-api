# pylint: disable=R0903
import datetime
from typing import Tuple, Optional, List, Mapping, Callable
import attr
import pydash
from ebl.fragmentarium.lemmatization import Lemmatization, LemmatizationError
from ebl.fragmentarium.language import Language
from ebl.fragmentarium.line import Line, ControlLine, EmptyLine, TextLine
from ebl.fragmentarium.token import Token, Word, LanguageShift
from ebl.fragmentarium.transliteration import Transliteration


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
class Text:
    lines: Tuple[Line, ...] = tuple()

    def to_dict(self) -> dict:
        return {
            'lines': [line.to_dict() for line in self.lines]
        }

    @staticmethod
    def from_dict(data: dict):
        token_factories: Mapping[str, Callable[[dict], Token]] = {
            'Token': lambda data: Token(
                data['value']
            ),
            'Word': lambda data: Word(
                data['value'],
                Language[data['language']],
                data['normalized'],
                tuple(data['uniqueLemma']),
            ),
            'LanguageShift': lambda data: LanguageShift(
                data['value']
            )
        }

        def create_tokens(content: List[dict]):
            return tuple(
                token_factories[token['type']](token)
                for token
                in content
            )
        line_factories: Mapping[str, Callable[[str, List[dict]], Line]] = {
            'ControlLine':
                lambda prefix, content: ControlLine(
                    prefix, create_tokens(content)
                ),
            'TextLine':
                lambda prefix, content: TextLine(
                    prefix, create_tokens(content)
                ),
            'EmptyLine':
                lambda _prefix, _content: EmptyLine()
        }
        lines = tuple(
            line_factories[line['type']](line['prefix'], line['content'])
            for line
            in data['lines']
        )
        return Text(lines)


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
    lemmatization: Lemmatization = Lemmatization([])
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

        return attr.evolve(
            self,
            lemmatization=lemmatization,
            notes=transliteration.notes,
            signs=transliteration.signs,
            record=record
        )

    def add_matching_lines(self, query) -> 'Fragment':
        matching_lines = query.get_matching_lines(self.transliteration)
        return attr.evolve(
            self,
            matching_lines=matching_lines
        )

    def update_lemmatization(self, lemmatization) -> 'Fragment':
        if self.lemmatization.is_compatible(lemmatization):
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
            'lemmatization': self.lemmatization.tokens,
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
            Lemmatization(data['lemmatization']),
            Text.from_dict(data['text']),
            data.get('signs'),
            data['notes'],
            data.get('hits'),
            data.get('matching_lines')
        )

from typing import Dict, List, NewType, Optional, Tuple, Union

import attr
import pydash

from ebl.auth0 import User
from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.application.transliteration_update import (
    TransliterationUpdate
)
from ebl.fragmentarium.domain.folios import Folios
from ebl.fragmentarium.domain.record import Record
from ebl.transliteration.lemmatization import Lemmatization
from ebl.transliteration.text import Text

FragmentNumber = NewType('FragmentNumber', str)


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Tuple[int, ...] = tuple()

    def to_dict(self) -> Dict[str, Union[str, List[int]]]:
        return attr.asdict(self)


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Union[str, float]]:
        return attr.asdict(self, filter=lambda _, value: value is not None)


@attr.s(auto_attribs=True, frozen=True)
class Fragment:
    number: FragmentNumber
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
    text: Text = Text()
    signs: Optional[str] = None
    notes: str = ''
    references: Tuple[Reference, ...] = tuple()
    uncurated_references: Optional[Tuple[UncuratedReference, ...]] = None

    def set_references(self, references: Tuple[Reference, ...]) -> 'Fragment':
        return attr.evolve(
            self,
            references=references
        )

    def update_transliteration(self,
                               transliteration: TransliterationUpdate,
                               user: User) -> 'Fragment':
        record = self.record.add_entry(
            self.text.atf,
            transliteration.atf,
            user
        )

        text = self.text.merge(transliteration.parse())

        return attr.evolve(
            self,
            text=text,
            notes=transliteration.notes,
            signs=transliteration.signs,
            record=record
        )

    def update_lemmatization(self, lemmatization: Lemmatization) -> 'Fragment':
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(
            self,
            text=text
        )

    def to_dict(self, with_dependencies=False) -> dict:
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
            'text': self.text.to_dict(),
            'references': [
                reference.to_dict(with_dependencies)
                for reference in self.references
            ],
            'uncuratedReferences': (
                [
                    reference.to_dict()
                    for reference
                    in self.uncurated_references
                ]
                if self.uncurated_references is not None
                else None
            )
        }, lambda value: value is None)

    def to_dict_for(self, user) -> dict:
        return {
            **self.to_dict(),
            'folios': self.folios.filter(user).to_list()
        }

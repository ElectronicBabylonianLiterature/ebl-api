# pylint: disable=R0903
from typing import Tuple, Optional, Dict, List, Union
import attr
import pydash
from ebl.bibliography.reference import Reference
from ebl.text.lemmatization import Lemmatization
from ebl.text.atf import AtfSyntaxError
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text
from ebl.fragment.folios import Folios
from ebl.fragment.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragment.record import Record


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
    text: Text = Text()
    signs: Optional[str] = None
    notes: str = ''
    hits: Optional[int] = None
    matching_lines: Optional[tuple] = None
    references: Tuple[Reference, ...] = tuple()
    uncurated_references: Optional[Tuple[UncuratedReference, ...]] = None

    def set_references(self, references: Tuple[Reference, ...]) -> 'Fragment':
        return attr.evolve(
            self,
            references=references
        )

    def update_transliteration(self, transliteration, user) -> 'Fragment':
        record = self.record.add_entry(
            self.text.atf,
            transliteration.atf,
            user
        )

        try:
            text = self.text.merge(parse_atf(transliteration.atf))

            return attr.evolve(
                self,
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
        matching_lines = query.get_matching_lines(
            Transliteration(self.text.atf, self.notes, self.signs)
        )
        return attr.evolve(
            self,
            matching_lines=matching_lines
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
            'hits': self.hits,
            'matching_lines': self.matching_lines,
            'references': [
                reference.to_dict(with_dependencies)
                for reference in self.references
            ],
            'uncurated_references': (
                [
                    reference.to_dict()
                    for reference
                    in self.uncurated_references  # pylint: disable=E1133
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

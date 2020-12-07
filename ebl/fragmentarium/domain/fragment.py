from typing import Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.application.create_line_to_vec import (
    create_line_to_vec,
    LineToVecEncodings,
)
from ebl.fragmentarium.domain.folios import Folios
from ebl.fragmentarium.domain.genres import genres
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.record import Record
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.text import Text
from ebl.users.domain.user import User


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Sequence[int] = tuple()


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Genre:
    category: Sequence[str] = attr.ib()
    uncertain: bool

    @category.validator
    def _check_is_genres_valid(self, _, category: Sequence[str]) -> None:
        category = tuple(category)
        if category not in genres:
            raise ValueError(f"'{category}' is not a valid genre")


@attr.s(auto_attribs=True, frozen=True)
class Fragment:
    number: MuseumNumber
    accession: str = ""
    cdli_number: str = ""
    bm_id_number: str = ""
    publication: str = ""
    description: str = ""
    collection: str = ""
    script: str = ""
    museum: str = ""
    width: Measure = Measure()
    length: Measure = Measure()
    thickness: Measure = Measure()
    joins: Sequence[str] = tuple()
    record: Record = Record()
    folios: Folios = Folios()
    text: Text = Text()
    signs: str = ""
    notes: str = ""
    references: Sequence[Reference] = tuple()
    uncurated_references: Optional[Sequence[UncuratedReference]] = None
    genres: Sequence[Genre] = tuple()
    line_to_vec: Optional[LineToVecEncodings] = None

    def set_references(self, references: Sequence[Reference]) -> "Fragment":
        return attr.evolve(self, references=references)

    def update_transliteration(
        self, transliteration: TransliterationUpdate, user: User
    ) -> "Fragment":
        record = self.record.add_entry(self.text.atf, transliteration.text.atf, user)

        text = self.text.merge(transliteration.text)

        return attr.evolve(
            self,
            text=text,
            notes=transliteration.notes,
            signs=transliteration.signs,
            record=record,
            line_to_vec=create_line_to_vec(text.lines),
        )

    def set_genres(self, genres_new: Sequence[Genre]) -> "Fragment":
        return attr.evolve(self, genres=tuple(genres_new))

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Fragment":
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(self, text=text)

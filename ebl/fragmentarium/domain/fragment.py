from typing import Optional, Sequence, Tuple

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.folios import Folios
from ebl.fragmentarium.domain.genres import genres

from ebl.fragmentarium.domain.record import Record
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.text import Text
from ebl.users.domain.user import User
from ebl.fragmentarium.domain.museum_number import MuseumNumber

Genre = Tuple[Tuple[str, ...], ...]


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Sequence[int] = tuple()


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None


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
    genre: Genre = attr.ib(default=tuple(tuple()))

    @genre.validator
    def _check_is_genre_valid(self, attribute, genre: Genre) -> bool:
        if not all(genre_elem in genres for genre_elem in genre):
            raise ValueError(f"All or parts of '{(genre)}' are not valid genres")

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
        )

    def set_genre(self, genre_retrieved: Sequence[Sequence[str]]) -> "Fragment":
        genre_retrieved = tuple(
            [tuple(single_genre) for single_genre in genre_retrieved]
        )
        self._check_is_genre_valid(genre_retrieved)
        return attr.evolve(self, genre=genre_retrieved)


    def update_lemmatization(self, lemmatization: Lemmatization) -> "Fragment":
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(self, text=text)

from typing import NewType, Optional, Tuple

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.folios import Folios
from ebl.fragmentarium.domain.record import Record
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.text import Text
from ebl.users.domain.user import User

FragmentNumber = NewType("FragmentNumber", str)


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Tuple[int, ...] = tuple()


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Fragment:
    number: FragmentNumber
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
    joins: Tuple[str, ...] = tuple()
    record: Record = Record()
    folios: Folios = Folios()
    text: Text = Text()
    signs: Optional[str] = None
    notes: str = ""
    references: Tuple[Reference, ...] = tuple()
    uncurated_references: Optional[Tuple[UncuratedReference, ...]] = None

    def set_references(self, references: Tuple[Reference, ...]) -> "Fragment":
        return attr.evolve(self, references=references)

    def update_transliteration(
        self, transliteration: TransliterationUpdate, user: User
    ) -> "Fragment":
        record = self.record.add_entry(self.text.atf, transliteration.atf, user)

        text = self.text.merge(transliteration.parse())

        return attr.evolve(
            self,
            text=text,
            notes=transliteration.notes,
            signs=transliteration.signs,
            record=record,
        )

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Fragment":
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(self, text=text)

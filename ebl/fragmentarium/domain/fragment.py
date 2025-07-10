from enum import Enum
from itertools import groupby
from typing import Dict, Any, Optional, Sequence, Tuple
import attr
import pydash
from ebl.fragmentarium.domain.museum import Museum
from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.accession import Accession
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.matches.create_line_to_vec import create_line_to_vec
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.folios import Folios
from ebl.fragmentarium.domain.genres import genres
from ebl.fragmentarium.domain.joins import Joins
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncodings
from ebl.fragmentarium.domain.record import Record
from ebl.fragmentarium.domain.token_annotation import TextLemmaAnnotation
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.users.domain.user import User
from marshmallow import ValidationError
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS
from ebl.transliteration.domain.lark_parser import parse_markup_paragraphs
from ebl.fragmentarium.domain.date import Date
from ebl.fragmentarium.domain.colophon import Colophon
from ebl.fragmentarium.domain.fragment_external_numbers import (
    FragmentExternalNumbers,
    ExternalNumbers,
)


def parse_markup_with_paragraphs(text: str) -> Sequence[MarkupPart]:
    try:
        return parse_markup_paragraphs(text) if text else ()
    except PARSE_ERRORS as error:
        raise ValidationError(f"Invalid markup: {text}. {error}") from error


class NotLowestJoinError(ValueError):
    pass


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Sequence[int] = ()
    search_term: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Acquisition:
    description: str = ""
    supplier: str = ""
    date: int = 0

    @staticmethod
    def of(source: Dict[str, Any]) -> "Acquisition":
        return Acquisition(
            description=source.get("description", ""),
            supplier=source.get("supplier", ""),
            date=source.get("date", 0),
        )


@attr.s(auto_attribs=True, frozen=True)
class Genre:
    category: Sequence[str] = attr.ib()
    uncertain: bool = False

    @category.validator
    def _check_is_genres_valid(self, _, category: Sequence[str]) -> None:
        category = tuple(category)
        if category not in genres:
            raise ValueError(f"'{category}' is not a valid genre")


@attr.s(auto_attribs=True, frozen=True)
class MarkupText:
    text: str = ""
    parts: Sequence[MarkupPart] = ()


@attr.s(auto_attribs=True, frozen=True)
class Introduction(MarkupText):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Notes(MarkupText):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Script:
    period: Period = attr.ib(default=Period.NONE)
    period_modifier: PeriodModifier = attr.ib(default=PeriodModifier.NONE)
    uncertain: bool = False

    def __str__(self) -> str:
        return self.abbreviation

    @property
    def abbreviation(self) -> str:
        return self.period.value[1]


@attr.s(auto_attribs=True, frozen=True)
class DossierReference:
    dossierId: str
    isUncertain: bool = False


@attr.s(auto_attribs=True, frozen=True)
class Fragment(FragmentExternalNumbers):
    number: MuseumNumber
    accession: Optional[Accession] = None
    publication: str = ""
    acquisition: Optional[Acquisition] = None
    description: str = ""
    cdli_images: Sequence[str] = []
    collection: str = ""
    legacy_script: str = ""
    museum: Museum = Museum.UNKNOWN
    width: Measure = Measure()
    length: Measure = Measure()
    thickness: Measure = Measure()
    joins: Joins = Joins()
    record: Record = Record()
    folios: Folios = Folios()
    text: Text = Text()
    signs: str = ""
    notes: Notes = Notes()
    references: Sequence[Reference] = ()
    uncurated_references: Optional[Sequence[UncuratedReference]] = None
    genres: Sequence[Genre] = ()
    line_to_vec: Tuple[LineToVecEncodings, ...] = ()
    authorized_scopes: Optional[Sequence[Scope]] = []
    introduction: Introduction = Introduction()
    script: Script = Script()
    date: Optional[Date] = None
    dates_in_text: Sequence[Date] = []
    projects: Sequence[str] = ()
    traditional_references: Sequence[str] = []
    archaeology: Optional[Archaeology] = None
    colophon: Optional[Colophon] = None
    external_numbers: ExternalNumbers = ExternalNumbers()
    dossiers: Sequence[str] = []

    @property
    def is_lowest_join(self) -> bool:
        return (self.joins.lowest or self.number) == self.number

    def set_references(self, references: Sequence[Reference]) -> "Fragment":
        return attr.evolve(self, references=references)

    def set_text(self, text: Text) -> "Fragment":
        return attr.evolve(self, text=text)

    def set_introduction(self, introduction: str) -> "Fragment":
        return attr.evolve(
            self,
            introduction=attr.evolve(
                self.introduction,
                text=introduction,
                parts=parse_markup_with_paragraphs(introduction),
            ),
        )

    def set_notes(self, notes: str) -> "Fragment":
        return attr.evolve(
            self,
            notes=attr.evolve(
                self.notes,
                text=notes,
                parts=parse_markup_with_paragraphs(notes),
            ),
        )

    def set_script(self, script: Script) -> "Fragment":
        return attr.evolve(self, script=script)

    def update_lowest_join_transliteration(
        self, transliteration: TransliterationUpdate, user: User
    ) -> "Fragment":
        if transliteration.text.is_empty or self.is_lowest_join:
            return self.update_transliteration(transliteration, user)
        else:
            raise NotLowestJoinError(
                "Transliteration must be empty unless fragment is the lowest in join."
            )

    def update_transliteration(
        self, transliteration: TransliterationUpdate, user: User
    ) -> "Fragment":
        record = self.record.add_entry(self.text.atf, transliteration.text.atf, user)
        text = self.text.merge(transliteration.text)

        text = text.set_token_ids()

        return attr.evolve(
            self,
            text=text,
            signs=transliteration.signs,
            record=record,
            line_to_vec=create_line_to_vec(text.lines),
        )

    def set_genres(self, genres_new: Sequence[Genre]) -> "Fragment":
        return attr.evolve(self, genres=tuple(genres_new))

    def set_scopes(self, scopes_new: Sequence[Enum]) -> "Fragment":
        return attr.evolve(self, authorized_scopes=list(scopes_new))

    def set_date(self, date_new: Optional[Date]) -> "Fragment":
        return attr.evolve(self, date=date_new)

    def set_dates_in_text(self, dates_in_text_new: Sequence[Date]) -> "Fragment":
        return attr.evolve(self, dates_in_text=dates_in_text_new)

    def set_archaeology(self, archaeology: Archaeology) -> "Fragment":
        return attr.evolve(self, archaeology=archaeology)

    def set_colophon(self, colophon: Colophon) -> "Fragment":
        return attr.evolve(self, colophon=colophon)

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Fragment":
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(self, text=text)

    def update_lemma_annotation(self, annotation: TextLemmaAnnotation) -> "Fragment":
        text = self.text.update_lemma_annotation(annotation)
        return attr.evolve(self, text=text)

    def get_matching_lines(self, query: TransliterationQuery) -> Text:
        line_numbers = query.match(self.signs)

        match = [
            (self.text.text_lines[numbers[0] : numbers[1] + 1])
            for numbers, _ in groupby(line_numbers)
        ]
        return Text(lines=tuple(pydash.flatten(match)))

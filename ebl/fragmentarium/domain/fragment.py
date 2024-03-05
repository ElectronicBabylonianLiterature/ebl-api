from itertools import groupby
from typing import Optional, Sequence, Tuple

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


def parse_markup_with_paragraphs(text: str) -> Sequence[MarkupPart]:
    try:
        return parse_markup_paragraphs(text) if text else tuple()
    except PARSE_ERRORS as error:
        raise ValidationError(f"Invalid markup: {text}. {error}") from error


class NotLowestJoinError(ValueError):
    pass


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
    uncertain: bool = False

    @category.validator
    def _check_is_genres_valid(self, _, category: Sequence[str]) -> None:
        category = tuple(category)
        if category not in genres:
            raise ValueError(f"'{category}' is not a valid genre")


@attr.s(auto_attribs=True, frozen=True)
class MarkupText:
    text: str = ""
    parts: Tuple[MarkupPart] = tuple()


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
class ExternalNumbers:
    cdli_number: str = ""
    bm_id_number: str = ""
    archibab_number: str = ""
    bdtns_number: str = ""
    ur_online_number: str = ""
    hilprecht_jena_number: str = ""
    hilprecht_heidelberg_number: str = ""
    metropolitan_number: str = ""
    louvre_number: str = ""
    alalah_hpm_number: str = ""
    australianinstituteofarchaeology_number: str = ""
    philadelphia_number: str = ""
    achemenet_number: str = ""
    nabucco_number: str = ""
    yale_peabody_number: str = ""
    oracc_numbers: Sequence[str] = tuple()
    seal_number: str = ""


@attr.s(auto_attribs=True, frozen=True)
class Fragment:
    number: MuseumNumber
    accession: Optional[Accession] = None
    publication: str = ""
    description: str = ""
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
    references: Sequence[Reference] = tuple()
    uncurated_references: Optional[Sequence[UncuratedReference]] = None
    genres: Sequence[Genre] = tuple()
    line_to_vec: Tuple[LineToVecEncodings, ...] = tuple()
    authorized_scopes: Optional[Sequence[Scope]] = list()
    introduction: Introduction = Introduction()
    script: Script = Script()
    date: Optional[Date] = None
    dates_in_text: Sequence[Date] = list()
    external_numbers: ExternalNumbers = ExternalNumbers()
    projects: Sequence[str] = tuple()
    traditional_references: Sequence[str] = list()
    archaeology: Optional[Archaeology] = None

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

        return attr.evolve(
            self,
            text=text,
            signs=transliteration.signs,
            record=record,
            line_to_vec=create_line_to_vec(text.lines),
        )

    def set_genres(self, genres_new: Sequence[Genre]) -> "Fragment":
        return attr.evolve(self, genres=tuple(genres_new))

    def set_date(self, date_new: Optional[Date]) -> "Fragment":
        return attr.evolve(self, date=date_new)

    def set_dates_in_text(self, dates_in_text_new: Sequence[Date]) -> "Fragment":
        return attr.evolve(self, dates_in_text=dates_in_text_new)

    def set_archaeology(self, archaeology: Archaeology) -> "Fragment":
        return attr.evolve(self, archaeology=archaeology)

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Fragment":
        text = self.text.update_lemmatization(lemmatization)
        return attr.evolve(self, text=text)

    def get_matching_lines(self, query: TransliterationQuery) -> Text:
        line_numbers = query.match(self.signs)

        match = [
            (self.text.text_lines[numbers[0] : numbers[1] + 1])
            for numbers, _ in groupby(line_numbers)
        ]
        return Text(lines=tuple(pydash.flatten(match)))

    def _get_external_number(self, number_type: str) -> str:
        return getattr(self.external_numbers, f"{number_type}_number")

    @property
    def cdli_number(self) -> str:
        return self._get_external_number("cdli")

    @property
    def bm_id_number(self) -> str:
        return self._get_external_number("bm_id")

    @property
    def archibab_number(self) -> str:
        return self._get_external_number("archibab")

    @property
    def bdtns_number(self) -> str:
        return self._get_external_number("bdtns")

    @property
    def ur_online_number(self) -> str:
        return self._get_external_number("ur_online")

    @property
    def hilprecht_jena_number(self) -> str:
        return self._get_external_number("hilprecht_jena")

    @property
    def hilprecht_heidelberg_number(self) -> str:
        return self._get_external_number("hilprecht_heidelberg")

    @property
    def yale_peabody_number(self) -> str:
        return self._get_external_number("yale_peabody")

    @property
    def metropolitan_number(self) -> str:
        return self._get_external_number("metropolitan_number")

    @property
    def louvre_number(self) -> str:
        return self._get_external_number("louvre_number")

    @property
    def alalah_hpm_number(self) -> str:
        return self._get_external_number("alalah_hpm_number")

    @property
    def australianinstituteofarchaeology_number(self) -> str:
        return self._get_external_number("australianinstituteofarchaeology_number")

    @property
    def achemenet_number(self) -> str:
        return self._get_external_number("achemenet")

    @property
    def nabucco_number(self) -> str:
        return self._get_external_number("nabucco")

    @property
    def philadelphia_number(self) -> str:
        return self._get_external_number("philadelphia_number")

    @property
    def seal_number(self) -> str:
        return self._get_external_number("seal_number")

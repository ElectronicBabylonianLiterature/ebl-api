from itertools import groupby
from typing import List, Optional, Sequence, Tuple
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
from ebl.fragmentarium.domain.joins import Joins
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncodings
from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntity,
    RealiaAnnotationSpan,
    RealiaEntity,
    deduplicate_spans,
)
from ebl.fragmentarium.domain.fragment_metadata import (
    Acquisition,
    DossierReference,
    Genre,
    Introduction,
    Measure,
    NotLowestJoinError,
    Notes,
    Script,
    UncuratedReference,
    parse_markup_with_paragraphs,
    to_named_entity_tuple,
    to_realia_tuple,
)
from ebl.fragmentarium.domain.record import Record
from ebl.fragmentarium.domain.token_annotation import TextLemmaAnnotation
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.word_tokens import AbstractWord
from ebl.users.domain.user import User
from ebl.fragmentarium.domain.date import Date
from ebl.fragmentarium.domain.colophon import Colophon
from ebl.fragmentarium.domain.fragment_external_numbers import (
    FragmentExternalNumbers,
    ExternalNumbers,
)

__all__ = [
    "Acquisition",
    "DossierReference",
    "Fragment",
    "Genre",
    "Introduction",
    "Measure",
    "NotLowestJoinError",
    "Notes",
    "Period",
    "PeriodModifier",
    "Script",
    "UncuratedReference",
    "parse_markup_with_paragraphs",
    "to_named_entity_tuple",
    "to_realia_tuple",
]


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
    ocred_signs: str = ""
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
    named_entities: Sequence[NamedEntity] = attr.ib(
        default=(), converter=to_named_entity_tuple
    )
    realia: Sequence[RealiaEntity] = attr.ib(default=(), converter=to_realia_tuple)

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

    def set_scopes(self, scopes_new: Sequence[Scope]) -> "Fragment":
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
            self.text.text_lines[slice(numbers[0], numbers[1] + 1)]
            for numbers, _ in groupby(line_numbers)
        ]
        return Text(lines=tuple(pydash.flatten(match)))

    def set_named_entities(
        self,
        entity_spans: Sequence[EntityAnnotationSpan],
        realia_spans: Sequence[RealiaAnnotationSpan] = (),
    ) -> "Fragment":
        unique_entities = deduplicate_spans(entity_spans)
        unique_realia = deduplicate_spans(realia_spans)
        return attr.evolve(
            self,
            named_entities=tuple(span.to_named_entity() for span in unique_entities),
            realia=tuple(span.to_realia_entity() for span in unique_realia),
            text=self.text.set_named_entities(unique_entities, unique_realia),
        )

    @property
    def words(self) -> List[AbstractWord]:
        return [
            token
            for line in self.text.text_lines
            for token in line.content
            if isinstance(token, AbstractWord)
        ]

    def get_word_by_id(self, word_id: str) -> AbstractWord:
        for word in self.words:
            if word.id_ == word_id:
                return word
        raise ValueError(f"Word with id {word_id} not found in fragment.")

    def set_token_ids(self) -> "Fragment":
        return attr.evolve(
            self,
            text=self.text.set_token_ids(),
        )

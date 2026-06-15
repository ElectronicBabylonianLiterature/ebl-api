from typing import Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.accession import Accession
from ebl.common.domain.project import ResearchProject
from ebl.fragmentarium.domain.date import Date
from ebl.fragmentarium.domain.fragment import DossierReference, Genre, Script
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text


@attr.s(auto_attribs=True, frozen=True)
class FragmentQueryArchaeology:
    excavation_number: Optional[MuseumNumber] = None
    site: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True, eq=False)
class FragmentQuerySummary:
    museum_number: MuseumNumber
    description: str
    script: Script
    matching_lines: Sequence[int] = ()
    matching_line_preview: Text = attr.Factory(Text)
    match_count: int = 0
    has_photo: bool = False
    accession: Optional[Accession] = None
    date: Optional[Date] = None
    genres: Sequence[Genre] = ()
    archaeology: Optional[FragmentQueryArchaeology] = None
    references: Sequence[Reference] = ()
    projects: Sequence[ResearchProject] = ()
    dossiers: Sequence[DossierReference] = ()

    def __eq__(self, other):
        if isinstance(other, FragmentQuerySummary):
            return (
                self.museum_number == other.museum_number
                and self.description == other.description
                and self.script == other.script
                and tuple(self.matching_lines) == tuple(other.matching_lines)
                and self.matching_line_preview == other.matching_line_preview
                and self.match_count == other.match_count
                and self.has_photo == other.has_photo
                and self.accession == other.accession
                and self.date == other.date
                and tuple(self.genres) == tuple(other.genres)
                and self.archaeology == other.archaeology
                and tuple(self.references) == tuple(other.references)
                and tuple(self.projects) == tuple(other.projects)
                and tuple(self.dossiers) == tuple(other.dossiers)
            )

        try:
            other_museum_number = other.museum_number
            other_matching_lines = other.matching_lines
            other_match_count = other.match_count
        except AttributeError:
            return NotImplemented

        return (
            self.museum_number == other_museum_number
            and tuple(self.matching_lines) == tuple(other_matching_lines)
            and self.match_count == other_match_count
        )


@attr.s(auto_attribs=True, frozen=True, eq=False)
class FragmentQueryResult:
    items: Sequence[FragmentQuerySummary]
    match_count_total: int

    @staticmethod
    def create_empty() -> "FragmentQueryResult":
        return FragmentQueryResult([], 0)

    def __eq__(self, other):
        if isinstance(other, FragmentQueryResult):
            return (
                tuple(self.items) == tuple(other.items)
                and self.match_count_total == other.match_count_total
            )

        try:
            other_items = other.items
            other_match_count_total = other.match_count_total
        except AttributeError:
            return NotImplemented

        return (
            tuple(self.items) == tuple(other_items)
            and self.match_count_total == other_match_count_total
        )

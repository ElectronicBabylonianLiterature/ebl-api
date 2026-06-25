from typing import Any, Dict, Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.accession import Accession
from ebl.common.domain.project import ResearchProject
from ebl.common.query.query_result import compare_query_results
from ebl.fragmentarium.domain.date import Date
from ebl.fragmentarium.domain.fragment import DossierReference, Genre, Script
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text


@attr.s(auto_attribs=True, frozen=True)
class FragmentQueryArchaeology:
    excavation_number: Optional[MuseumNumber] = None
    site: Optional[str] = None


def empty_matching_line_preview() -> Dict[str, Any]:
    return {"lines": (), "parser_version": DEFAULT_ATF_PARSER_VERSION}


def lightweight_token_of(token) -> Dict[str, Any]:
    data = {
        "value": token.value,
        "cleanValue": getattr(token, "clean_value", None),
        "uniqueLemma": [
            str(lemma) for lemma in getattr(token, "unique_lemma", ())
        ],
        "type": token.__class__.__name__,
    }
    return {
        key: value
        for key, value in data.items()
        if value is not None and (key != "uniqueLemma" or value)
    }


def lightweight_line_preview_of(line) -> Dict[str, Any]:
    content = getattr(line, "content", ())
    prefix = getattr(getattr(line, "line_number", None), "atf", "")
    return {
        "number": prefix,
        "prefix": prefix,
        "text": " ".join(token.value for token in content),
        "tokens": [lightweight_token_of(token) for token in content],
    }


@attr.s(auto_attribs=True, frozen=True, eq=False)
class FragmentQuerySummary:
    museum_number: MuseumNumber
    description: str
    script: Script
    matching_lines: Sequence[int] = ()
    matching_line_preview: Dict[str, Any] = attr.Factory(empty_matching_line_preview)
    match_count: int = 0
    has_photo: bool = False
    accession: Optional[Accession] = None
    date: Optional[Date] = None
    genres: Sequence[Genre] = ()
    archaeology: Optional[FragmentQueryArchaeology] = None
    references: Sequence[Reference] = ()
    projects: Sequence[ResearchProject] = ()
    dossiers: Sequence[DossierReference] = ()

    def _comparison_values(self):
        return (
            self.museum_number,
            self.description,
            self.script,
            tuple(self.matching_lines),
            self.matching_line_preview,
            self.match_count,
            self.has_photo,
            self.accession,
            self.date,
            tuple(self.genres),
            self.archaeology,
            tuple(self.references),
            tuple(self.projects),
            tuple(self.dossiers),
        )

    def __eq__(self, other):
        if isinstance(other, FragmentQuerySummary):
            return self._comparison_values() == other._comparison_values()

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


def matching_line_preview_of(text: Text, matching_lines: Sequence[int]) -> Dict[str, Any]:
    return {
        "lines": [
            lightweight_line_preview_of(text.lines[index]) for index in matching_lines
        ],
        "parser_version": text.parser_version or DEFAULT_ATF_PARSER_VERSION,
    }


@attr.s(auto_attribs=True, frozen=True, eq=False)
class FragmentQueryResult:
    items: Sequence[FragmentQuerySummary]
    match_count_total: Optional[int]
    is_match_count_total_exact: bool = True
    has_next_page: Optional[bool] = None
    show_count_metadata: bool = False

    @staticmethod
    def create_empty() -> "FragmentQueryResult":
        return FragmentQueryResult([], 0)

    def __eq__(self, other):
        return compare_query_results(self, other)

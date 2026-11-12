from typing import Sequence

import attr


@attr.s(frozen=True, auto_attribs=True)
class SumerianWordSummary:
    id: str
    citation_form: str
    homonym: str
    guide_word: str
    pos: str
    attinger_pos: str
    language: str
    cuneiform: str
    french_senses: Sequence[str]
    english_senses: Sequence[str]
    has_attinger: bool
    has_epsd2: bool
    epsd2_form_count: int
    akkadian_count: int
    citation_count: int
    compound_count: int
    cross_reference_count: int
    has_emesal: bool
    attestation_count: int
    matched_alias: str = ""


@attr.s(frozen=True, auto_attribs=True)
class SearchResult:
    total: int
    entries: Sequence[SumerianWordSummary]


@attr.s(frozen=True, auto_attribs=True)
class Statistics:
    lemmas: int
    attinger: int
    aligned: int
    epsd2_only: int
    proper_nouns: int
    with_akkadian: int

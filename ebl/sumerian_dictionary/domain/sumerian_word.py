from typing import Optional, Sequence, Tuple

import attr

from ebl.sumerian_dictionary.domain.sumerian_word_links import (
    Alias,
    CrossReference,
    WordLink,
)


@attr.s(frozen=True, auto_attribs=True)
class AttingerSense:
    meaning: str
    lang: str
    entry_id: str


@attr.s(frozen=True, auto_attribs=True)
class Epsd2Sense:
    num: str
    meaning: str
    lang: str


@attr.s(frozen=True, auto_attribs=True)
class AttingerForm:
    spelling: str
    non_standard: bool
    attestations: str = ""


@attr.s(frozen=True, auto_attribs=True)
class Epsd2Form:
    spelling: str
    count: int
    percent: float


@attr.s(frozen=True, auto_attribs=True)
class EmesalForm:
    form: str
    source: str


@attr.s(frozen=True, auto_attribs=True)
class SignSpelling:
    source: str
    spelling: str


@attr.s(frozen=True, auto_attribs=True)
class SignEntry:
    reading: str
    name: str
    utf8: str
    ambiguous: bool
    sources: Sequence[SignSpelling]
    sign_list: str = ""
    character_list: str = ""
    known_wrong_character: bool = False
    determinative: bool = False
    unresolved: bool = False
    form_of: Sequence[str] = ()


@attr.s(frozen=True, auto_attribs=True)
class UnrenderedToken:
    token: str
    reason: str


@attr.s(frozen=True, auto_attribs=True)
class Rendering:
    spelling: str
    source: str
    kind: str
    cuneiform: Sequence[str]
    complete: bool
    sign_lists: Sequence[str] = ()
    unrendered: Sequence[UnrenderedToken] = ()
    printed: str = ""
    known_wrong_characters: Sequence[str] = ()


@attr.s(frozen=True, auto_attribs=True)
class Citation:
    work: str
    passage: str = ""
    etcsl: str = ""
    composition_id: str = ""


@attr.s(frozen=True, auto_attribs=True)
class AkkadianEquivalent:
    word_id: str
    source: str
    index_numbers: str = ""


@attr.s(frozen=True, auto_attribs=True)
class Attestation:
    count: int = 0
    periods: Sequence[str] = ()


@attr.s(frozen=True, auto_attribs=True)
class AttingerHeadword:
    text: str
    display: str
    marks: Sequence[Tuple[int, int, str]] = ()


@attr.s(frozen=True, auto_attribs=True)
class AttingerSource:
    entry_id: str
    node: str
    letter: str
    depth: int
    part_of_speech: str
    headword: AttingerHeadword


@attr.s(frozen=True, auto_attribs=True)
class Epsd2Source:
    oid: str
    headword: str
    builds: Sequence[str] = ()


@attr.s(frozen=True, auto_attribs=True)
class Sources:
    attinger: Optional[AttingerSource] = None
    epsd2: Optional[Epsd2Source] = None


@attr.s(frozen=True, auto_attribs=True)
class Match:
    tier: str
    method: str
    spelling: str
    candidate_count: int
    curated: bool
    curated_oid: str = ""
    curated_status: str = ""
    oid_status: str = ""
    review: Sequence[str] = ()


@attr.s(frozen=True, auto_attribs=True)
class SumerianWord:
    id: str
    citation_form: str
    lemma: Sequence[str]
    homonym: str
    guide_word: str
    pos: str
    attinger_pos: str
    language: str
    uncertain: bool
    stems: Sequence[str]
    determinatives: Sequence[str]
    case_frame: Sequence[str]
    emesal: Sequence[EmesalForm]
    attinger_senses: Sequence[AttingerSense]
    epsd2_senses: Sequence[Epsd2Sense]
    attinger_forms: Sequence[AttingerForm]
    epsd2_forms: Sequence[Epsd2Form]
    signs: Sequence[SignEntry]
    renderings: Sequence[Rendering]
    head: Optional[WordLink]
    compounds: Sequence[WordLink]
    name_compounds: Sequence[WordLink]
    cross_references: Sequence[CrossReference]
    aliases: Sequence[Alias]
    akkadian_equivalents: Sequence[AkkadianEquivalent]
    citations: Sequence[Citation]
    attestation: Attestation
    sources: Sources
    match: Match
    atf: str = ""
    truncated: bool = False

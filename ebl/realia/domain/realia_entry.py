import attr
from typing import Optional, Sequence

from ebl.bibliography.domain.reference import Reference


@attr.s(frozen=True, auto_attribs=True)
class CrossReference:
    id: str
    lemma: str


@attr.s(frozen=True, auto_attribs=True)
class AfoCrossReference:
    id: str
    lemma: str
    afo_volume: str = ""
    page: str = ""


@attr.s(frozen=True, auto_attribs=True)
class AfoRegisterEntry:
    main_word: str = ""
    note: str = ""
    afo: str = ""
    reference: str = ""
    cross_reference: str = ""
    afo_volume: str = ""
    page: str = ""
    cross_references: Sequence[AfoCrossReference] = ()


@attr.s(frozen=True, auto_attribs=True)
class ReallexikonEntry:
    id: str = ""
    title: str = ""
    reference: Optional[Reference] = None


@attr.s(frozen=True, auto_attribs=True)
class RealiaEntry:
    id: str
    realia_id: str = ""
    related_terms: Sequence[str] = ()
    type: Sequence[str] = ()
    afo_register: Sequence[AfoRegisterEntry] = ()
    references: Sequence[Reference] = ()
    wikidata_id: Sequence[str] = ()
    reallexikon: Sequence[ReallexikonEntry] = ()
    cross_references: Sequence[CrossReference] = ()
    afo_cross_references: Sequence[AfoCrossReference] = ()

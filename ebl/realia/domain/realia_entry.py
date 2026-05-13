import attr
from typing import Optional, Sequence

from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.named_enum import NamedEnum


class RealiaType(NamedEnum):
    BUILDING_NAME = ("BUILDING_NAME", "BN")
    CELESTIAL_NAME = ("CELESTIAL_NAME", "CN")
    DIVINE_NAME = ("DIVINE_NAME", "DN")
    ETHNOS_NAME = ("ETHNOS_NAME", "EN")
    FIELD_NAME = ("FIELD_NAME", "FN")
    GEOGRAPHICAL_NAME = ("GEOGRAPHICAL_NAME", "GN")
    MONTH_NAME = ("MONTH_NAME", "MN")
    OBJECT_NAME = ("OBJECT_NAME", "ON")
    PERSONAL_NAME = ("PERSONAL_NAME", "PN")
    ROYAL_NAME = ("ROYAL_NAME", "RN")
    WATERCOURSE_NAME = ("WATERCOURSE_NAME", "WN")
    YEAR_NAME = ("YEAR_NAME", "YN")


@attr.s(frozen=True, auto_attribs=True)
class AfoRegisterEntry:
    main_word: str = ""
    note: str = ""
    afo: str = ""
    reference: str = ""
    cross_reference: str = ""


@attr.s(frozen=True, auto_attribs=True)
class ReallexikonEntry:
    id: str = ""
    title: str = ""
    reference: Optional[Reference] = None
    content: str = ""


@attr.s(frozen=True, auto_attribs=True)
class RealiaEntry:
    id: str
    related_terms: Sequence[str] = ()
    type: Sequence[RealiaType] = ()
    afo_register: Sequence[AfoRegisterEntry] = ()
    references: Sequence[Reference] = ()
    wikidata_id: Sequence[str] = ()
    reallexikon: Sequence[ReallexikonEntry] = ()

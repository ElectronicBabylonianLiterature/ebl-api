from typing import Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.siglum_enum import SiglumEnum, SiglumEnumWithParent
from ebl.fragmentarium.domain.joins import Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine


class ManuscriptType(SiglumEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    COMMENTARY = ("Commentary", "Com")
    QUOTATION = ("Quotation", "Quo")
    EXCERPT = ("Excerpt", "Ex")
    PARALLEL = ("Parallel", "Par")
    NONE = ("None", "")


class Provenance(SiglumEnumWithParent):
    STANDARD_TEXT = ("Standard Text", "Std", None)
    ASSYRIA = ("Assyria", "Assa", None)
    ASSUR = ("Aššur", "Ašš", "Assyria")
    HUZIRINA = ("Ḫuzirina", "Huz", "Assyria")
    KALHU = ("Kalḫu", "Kal", "Assyria")
    KHORSABAD = ("Khorsabad", "Kho", "Assyria")
    NINEVEH = ("Nineveh", "Nin", "Assyria")
    TARBISU = ("Tarbiṣu", "Tar", "Assyria")
    BABYLONIA = ("Babylonia", "Baba", None)
    BABYLON = ("Babylon", "Bab", "Babylonia")
    BORSIPPA = ("Borsippa", "Bor", "Babylonia")
    CUTHA = ("Cutha", "Cut", "Babylonia")
    DILBAT = ("Dilbat", "Dil", "Babylonia")
    ISIN = ("Isin", "Isn", "Babylonia")
    KIS = ("Kiš", "Kiš", "Babylonia")
    LARSA = ("Larsa", "Lar", "Babylonia")
    METURAN = ("Meturan", "Met", "Babylonia")
    NEREBUN = ("Nērebtum", "Nēr", "Babylonia")
    NIPPUR = ("Nippur", "Nip", "Babylonia")
    SIPPAR = ("Sippar", "Sip", "Babylonia")
    SADUPPUM = ("Šaduppûm", "Šad", "Babylonia")
    UR = ("Ur", "Ur", "Babylonia")
    URUK = ("Uruk", "Urk", "Babylonia")
    PERIPHERY = ("Periphery", "", None)
    ALALAKS = ("Alalakh", "Ala", "Periphery")
    TELL_EL_AMARNA = ("Tell el-Amarna", "Ama", "Periphery")
    EMAR = ("Emar", "Emr", "Periphery")
    HATTUSA = ("Ḫattuša", "Hat", "Periphery")
    MARI = ("Mari", "Mar", "Periphery")
    MEGIDDO = ("Megiddo", "Meg", "Periphery")
    SUSA = ("Susa", "Sus", "Periphery")
    UGARIT = ("Ugarit", "Uga", "Periphery")
    UNCERTAIN = ("Uncertain", "Unc", None)


@attr.s(auto_attribs=True, frozen=True)
class Siglum:
    provenance: Provenance
    period: Period
    type: ManuscriptType
    disambiquator: str

    def __str__(self) -> str:
        return "".join(
            [
                self.provenance.abbreviation,
                self.period.abbreviation,
                self.type.abbreviation,
                self.disambiquator,
            ]
        )


@attr.s(auto_attribs=True, frozen=True)
class OldSiglum:
    siglum: str
    reference: Reference


def is_invalid_standard_text(provenance, period, type_) -> bool:
    return provenance is Provenance.STANDARD_TEXT and (
        period is not Period.NONE or type_ is not ManuscriptType.NONE
    )


def is_invalid_non_standard_text(provenance, period, type_) -> bool:
    return provenance is not Provenance.STANDARD_TEXT and (
        period is Period.NONE or type_ is ManuscriptType.NONE
    )


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    id: int
    siglum_disambiguator: str = ""
    old_sigla: Sequence[OldSiglum] = tuple()
    museum_number: Optional[MuseumNumber] = None
    accession: str = attr.ib(default="")
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = attr.ib(default=Provenance.NINEVEH)
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ""
    colophon: Text = Text()
    unplaced_lines: Text = Text()
    references: Sequence[Reference] = tuple()
    joins: Joins = Joins()
    is_in_fragmentarium: bool = False

    @accession.validator
    def validate_accession(self, _, value) -> None:
        if self.museum_number and value:
            raise ValueError("Accession given when museum number present.")

    @provenance.validator
    def validate_provenance(self, _, value) -> None:
        if is_invalid_standard_text(value, self.period, self.type):
            raise ValueError(
                "Manuscript must not have period and type when provenance is Standard Text."
            )
        elif is_invalid_non_standard_text(value, self.period, self.type):
            raise ValueError(
                "Manuscript must have period and type unless provenance is Standard Text."
            )

    @property
    def text_lines(self) -> Sequence[TextLine]:
        return [*self.colophon.text_lines, *self.unplaced_lines.text_lines]

    @property
    def siglum(self) -> Siglum:
        return Siglum(
            self.provenance, self.period, self.type, self.siglum_disambiguator
        )

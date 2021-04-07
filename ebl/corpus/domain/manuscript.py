from enum import Enum
from typing import Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine


class SiglumEnum(Enum):
    def __init__(self, long_name, abbreviation):
        self.long_name = long_name
        self.abbreviation = abbreviation

    @classmethod
    def from_abbreviation(cls, abbreviation):
        return [enum for enum in cls if enum.abbreviation == abbreviation][0]

    @classmethod
    def from_name(cls, name):
        return [enum for enum in cls if enum.long_name == name][0]


class SiglumEnumWithParent(SiglumEnum):
    def __init__(self, long_name, abbreviation, parent):
        super().__init__(long_name, abbreviation)
        self.parent = parent


class ManuscriptType(SiglumEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    COMMENTARY = ("Commentary", "Com")
    QUOTATION = ("Quotation", "Quo")
    EXCERPT = ("Excerpt", "Ex")
    PARALLEL = ("Parallel", "Par")


class Provenance(SiglumEnumWithParent):
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


class PeriodModifier(Enum):
    NONE = "None"
    EARLY = "Early"
    LATE = "Late"


class Period(SiglumEnumWithParent):
    UR_III = ("Ur III", "Ur3", None)
    OLD_ASSYRIAN = ("Old Assyrian", "OA", None)
    OLD_BABYLONIAN = ("Old Babylonian", "OB", None)
    MIDDLE_BABYLONIAN = ("Middle Babylonian", "MB", None)
    MIDDLE_ASSYRIAN = ("Middle Assyrian", "MA", None)
    HITTITE = ("Hittite", "Hit", None)
    NEO_ASSYRIAN = ("Neo-Assyrian", "NA", None)
    NEO_BABYLONIAN = ("Neo-Babylonian", "NB", None)
    LATE_BABYLONIAN = ("Late Babylonian", "LB", None)
    PERSIAN = ("Persian", "Per", "Late Babylonian")
    HELLENISTIC = ("Hellenistic", "Hel", "Late Babylonian")
    PARTHIAN = ("Parthian", "Par", "Late Babylonian")
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
class Manuscript:
    id: int
    siglum_disambiguator: str = ""
    museum_number: Optional[MuseumNumber] = None
    accession: str = attr.ib(default="")
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = Provenance.NINEVEH
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ""
    colophon: Text = Text()
    references: Sequence[Reference] = tuple()

    @accession.validator
    def validate_accession(self, _, value) -> None:
        if self.museum_number and value:
            raise ValueError("Accession given when museum number present.")

    @property
    def colophon_text_lines(self) -> Sequence[TextLine]:
        return self.colophon.text_lines

    @property
    def siglum(self) -> Siglum:
        return Siglum(
            self.provenance, self.period, self.type, self.siglum_disambiguator
        )

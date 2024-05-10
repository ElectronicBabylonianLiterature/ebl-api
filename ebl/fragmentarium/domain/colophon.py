import attr
from typing import Optional, List
from enum import Enum


class ColophonStatus(Enum):
    Yes = "Yes"
    No = "No"
    Broken = "Broken"
    OnlyColophon = "Only Colophon"


class ColophonType(Enum):
    AsbA = "Asb a"
    AsbB = "Asb b"
    AsbC = "Asb c"
    AsbD = "Asb d"
    AsbE = "Asb e"
    AsbF = "Asb f"
    AsbG = "Asb g BAK 321"
    AsbH = "Asb h"
    AsbI = "Asb i"
    AsbK = "Asb k"
    AsbL = "Asb l"
    AsbM = "Asb m"
    AsbN = "Asb n"
    AsbO = "Asb o"
    AsbP = "Asb p"
    AsbQ = "Asb q"
    AsbRS = "Asb r/s"
    AsbT = "Asb t"
    AsbU = "Asb u"
    AsbV = "Asb v"
    AsbW = "Asb w"
    AsbUnclear = "Asb Unclear"
    NzkBAK293 = "Nzk BAK 293"
    NzkBAK294 = "Nzk BAK 294"
    NzkBAK295 = "Nzk BAK 295"
    NzkBAK296 = "Nzk BAK 296"
    NzkBAK297 = "Nzk BAK 297"


class ColophonOwnership(Enum):
    Library = "Library"
    Private = "Private"
    Individual = "Individual"


class IndividualType(Enum):
    Owner = "Owner"
    Scribe = "Scribe"
    Other = "Other"


@attr.s(auto_attribs=True, frozen=True)
class NameAttestation:
    value: Optional[str] = None
    is_broken: Optional[bool] = None
    is_uncertain: Optional[bool] = None


@attr.s(auto_attribs=True, frozen=True)
class ProvenanceAttestation:
    value: Optional[str] = None
    is_broken: Optional[bool] = None
    is_uncertain: Optional[bool] = None


@attr.s(auto_attribs=True, frozen=True)
class IndividualTypeAttestation:
    value: Optional[IndividualType] = None
    is_broken: Optional[bool] = None
    is_uncertain: Optional[bool] = None


@attr.s(auto_attribs=True, frozen=True)
class IndividualAttestation:
    name: Optional[NameAttestation] = None
    son_of: Optional[NameAttestation] = None
    grandson_of: Optional[NameAttestation] = None
    family: Optional[NameAttestation] = None
    native_of: Optional[ProvenanceAttestation] = None
    type: Optional[IndividualTypeAttestation] = None


@attr.s(auto_attribs=True, frozen=True)
class Colophon:
    colophon_status: Optional[ColophonStatus] = None
    colophon_ownership: Optional[ColophonOwnership] = None
    colophon_types: List[ColophonType] = attr.ib(factory=list)
    original_from: Optional[ProvenanceAttestation] = None
    written_in: Optional[ProvenanceAttestation] = None
    notes_to_scribal_process: Optional[str] = None
    individuals: List[IndividualAttestation] = attr.ib(factory=list)

from enum import Enum, unique
from typing import Mapping


@unique
class Stage(Enum):
    UNCERTAIN = "Uncertain"
    URUK_IV = "Uruk IV"
    URUK_III_JEMDET_NASR = "Uruk III-Jemdet Nasr"
    ED_I_II = "ED I-II"
    FARA = "Fara"
    PRESARGONIC = "Presargonic"
    SARGONIC = "Sargonic"
    UR_III = "Ur III"
    OLD_ASSYRIAN = "Old Assyrian"
    OLD_BABYLONIAN = "Old Babylonian"
    MIDDLE_BABYLONIAN = "Middle Babylonian"
    MIDDLE_ASSYRIAN = "Middle Assyrian"
    HITTITE = "Hittite"
    NEO_ASSYRIAN = "Neo-Assyrian"
    NEO_BABYLONIAN = "Neo-Babylonian"
    LATE_BABYLONIAN = "Late Babylonian"
    PERSIAN = "Persian"
    HELLENISTIC = "Hellenistic"
    PARTHIAN = "Parthian"
    PROTO_ELAMITE = "Proto-Elamite"
    OLD_ELAMITE = "Old Elamite"
    MIDDLE_ELAMITE = "Middle Elamite"
    NEO_ELAMITE = "Neo-Elamite"
    STANDARD_BABYLONIAN = "Standard Babylonian"

    @property
    def abbreviation(self) -> str:
        return ABBREVIATIONS[self]


ABBREVIATIONS: Mapping[Stage, str] = {
    Stage.UR_III: "Ur3",
    Stage.OLD_ASSYRIAN: "OA",
    Stage.OLD_BABYLONIAN: "OB",
    Stage.MIDDLE_BABYLONIAN: "MB",
    Stage.MIDDLE_ASSYRIAN: "MA",
    Stage.HITTITE: "Hit",
    Stage.NEO_ASSYRIAN: "NA",
    Stage.NEO_BABYLONIAN: "NB",
    Stage.LATE_BABYLONIAN: "LB",
    Stage.PERSIAN: "Per",
    Stage.HELLENISTIC: "Hel",
    Stage.PARTHIAN: "Par",
    Stage.UNCERTAIN: "Unc",
    Stage.URUK_IV: "Uruk4",
    Stage.URUK_III_JEMDET_NASR: "JN",
    Stage.ED_I_II: "ED1_2",
    Stage.FARA: "Fara",
    Stage.PRESARGONIC: "PSarg",
    Stage.SARGONIC: "Sarg",
    Stage.STANDARD_BABYLONIAN: "SB",
    Stage.PROTO_ELAMITE: "PElam",
    Stage.OLD_ELAMITE: "OElam",
    Stage.MIDDLE_ELAMITE: "MElam",
    Stage.NEO_ELAMITE: "NElam",
}

from enum import Enum, unique
from typing import Mapping


@unique
class Stage(Enum):
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
    UNCERTAIN = "Uncertain"
    URUK_IV = "Uruk IV"
    URUK_III_JEMDET_NASR = "Uruk III-Jemdet Nasr"
    ED_I_II = "ED I-II"
    FARA = "Fara"
    PRESARGONIC = "Presargonic"
    SARGONIC = "Sargonic"
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
    Stage.ED_I_II: "ED1-2",
    Stage.FARA: "Fara",
    Stage.PRESARGONIC: "PSarg",
    Stage.SARGONIC: "Sarg",
    Stage.STANDARD_BABYLONIAN: "SB",
}

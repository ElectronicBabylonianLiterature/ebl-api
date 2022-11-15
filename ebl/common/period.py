from enum import Enum
from ebl.common.siglum_enum import SiglumEnumWithParent


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
    NONE = ("None", "", None)
    URUK_IV = ("Uruk IV", "Uruk4", None)
    URUK_III_JEMDET_NASR = ("Uruk III-Jemdet Nasr", "JN", None)
    ED_I_II = ("ED I-II", "ED1_2", None)
    FARA = ("Fara", "Fara", None)
    PRESARGONIC = ("Presargonic", "PSarg", None)
    SARGONIC = ("Sargonic", "Sarg", None)


class PeriodModifier(Enum):
    NONE = "None"
    EARLY = "Early"
    LATE = "Late"

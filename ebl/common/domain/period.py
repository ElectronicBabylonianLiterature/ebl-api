from enum import Enum
from ebl.common.domain.named_enum import NamedEnumWithParent


class Period(NamedEnumWithParent):
    NONE = ("None", "", None, 0)
    UNCERTAIN = ("Uncertain", "Unc", None, 1)
    URUK_IV = ("Uruk IV", "Uruk4", None, 2)
    URUK_III_JEMDET_NASR = ("Uruk III-Jemdet Nasr", "JN", None, 3)
    ED_I_II = ("ED I-II", "ED1_2", None, 4)
    FARA = ("Fara", "Fara", None, 5)
    PRESARGONIC = ("Presargonic", "PSarg", None, 6)
    SARGONIC = ("Sargonic", "Sarg", None, 7)
    UR_III = ("Ur III", "Ur3", None, 8)
    OLD_ASSYRIAN = ("Old Assyrian", "OA", None, 9)
    OLD_BABYLONIAN = ("Old Babylonian", "OB", None, 10)
    MIDDLE_BABYLONIAN = ("Middle Babylonian", "MB", None, 11)
    MIDDLE_ASSYRIAN = ("Middle Assyrian", "MA", None, 12)
    HITTITE = ("Hittite", "Hit", None, 13)
    NEO_ASSYRIAN = ("Neo-Assyrian", "NA", None, 14)
    NEO_BABYLONIAN = ("Neo-Babylonian", "NB", None, 15)
    LATE_BABYLONIAN = ("Late Babylonian", "LB", None, 16)
    PERSIAN = ("Persian", "Per", "Late Babylonian", 17)
    HELLENISTIC = ("Hellenistic", "Hel", "Late Babylonian", 18)
    PARTHIAN = ("Parthian", "Par", "Late Babylonian", 19)
    PROTO_ELAMITE = ("Proto-Elamite", "PElam", None, 20)
    OLD_ELAMITE = ("Old Elamite", "OElam", None, 21)
    MIDDLE_ELAMITE = ("Middle Elamite", "MElam", None, 22)
    NEO_ELAMITE = ("Neo-Elamite", "NElam", None, 23)
    LUWIAN = ("Luwian", "Luw", None, 24)
    ARAMAIC = ("Aramaic", "Aram", None, 25)


class PeriodModifier(Enum):
    NONE = "None"
    EARLY = "Early"
    MIDDLE = "Middle"
    LATE = "Late"

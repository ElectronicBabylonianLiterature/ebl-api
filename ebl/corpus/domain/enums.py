from enum import Enum


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


class Classification(Enum):
    ANCIENT = "Ancient"
    MODERN = "Modern"


class ManuscriptType(SiglumEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    COMMENTARY = ("Commentary", "Com")
    QUOTATION = ("Quotation", "Quo")


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
    STANDARD_BABYLONIAN = "Standard Babylonian"

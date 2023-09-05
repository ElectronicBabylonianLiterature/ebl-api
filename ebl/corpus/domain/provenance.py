from ebl.common.domain.named_enum import NamedEnum


class ProvenanceEnum(NamedEnum):
    def __init__(self, long_name, abbreviation, parent, cigs_key, sort_key=-1):
        super().__init__(long_name, abbreviation, sort_key)
        self.parent = parent
        self.cigs_key = cigs_key


class Provenance(ProvenanceEnum):
    STANDARD_TEXT = ("Standard Text", "Std", None, None)
    ASSYRIA = ("Assyria", "Assa", None, None)
    ASSUR = ("Aššur", "Ašš", "Assyria", "ASS")
    HUZIRINA = ("Ḫuzirina", "Huz", "Assyria", "HUZ")
    KALHU = ("Kalḫu", "Kal", "Assyria", "NIM")
    KHORSABAD = ("Khorsabad", "Kho", "Assyria", "SAR")
    NINEVEH = ("Nineveh", "Nin", "Assyria", "NNV")
    TARBISU = ("Tarbiṣu", "Tar", "Assyria", "SKH")
    BABYLONIA = ("Babylonia", "Baba", None, None)
    BABYLON = ("Babylon", "Bab", "Babylonia", "BAB")
    BORSIPPA = ("Borsippa", "Bor", "Babylonia", "BOR")
    CUTHA = ("Cutha", "Cut", "Babylonia", "GUD")
    DILBAT = ("Dilbat", "Dil", "Babylonia", "DLB")
    ISIN = ("Isin", "Isn", "Babylonia", "ISN")
    KIS = ("Kiš", "Kiš", "Babylonia", "KSH")
    LARSA = ("Larsa", "Lar", "Babylonia", "LAR")
    METURAN = ("Meturan", "Met", "Babylonia", "HDD")
    NEREBUN = ("Nērebtum", "Nēr", "Babylonia", "NRB")
    NIPPUR = ("Nippur", "Nip", "Babylonia", "NIP")
    SIPPAR = ("Sippar", "Sip", "Babylonia", "SAP")
    SADUPPUM = ("Šaduppûm", "Šad", "Babylonia", "SDP")
    UR = ("Ur", "Ur", "Babylonia", "URI")
    URUK = ("Uruk", "Urk", "Babylonia", "URU")
    PERIPHERY = ("Periphery", "", None, None)
    ALALAKS = ("Alalakh", "Ala", "Periphery", "ALA")
    TELL_EL_AMARNA = ("Tell el-Amarna", "Ama", "Periphery", "AKH")
    EMAR = ("Emar", "Emr", "Periphery", "EMR")
    HATTUSA = ("Ḫattuša", "Hat", "Periphery", "HAT")
    MARI = ("Mari", "Mar", "Periphery", "MAR")
    MEGIDDO = ("Megiddo", "Meg", "Periphery", "MGD")
    SUSA = ("Susa", "Sus", "Periphery", "SUS")
    UGARIT = ("Ugarit", "Uga", "Periphery", "UGA")
    UNCERTAIN = ("Uncertain", "Unc", None, None)

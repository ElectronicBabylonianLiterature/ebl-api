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
    DUR_KATLIMMU = ("Dūr-Katlimmu", "Dka", "Assyria", "DKA")
    GUZANA = ("Guzana", "Guz", "Assyria", "HLF")
    HARRAN = ("Ḫarrān", "Har", "Assyria", "HAR")
    HUZIRINA = ("Ḫuzirina", "Huz", "Assyria", "HUZ")
    IMGUR_ENLIL = ("Imgur-Enlil", "Img", "Assyria", "BLW")
    KALHU = ("Kalḫu", "Kal", "Assyria", "NIM")
    KAR_TUKULTI_NINURTA = ("Kār-Tukulti-Ninurta", "Ktn", "Assyria", "KTN")
    KHORSABAD = ("Khorsabad", "Kho", "Assyria", "SAR")
    NINEVEH = ("Nineveh", "Nin", "Assyria", "NNV")
    SUBAT_ENLIL = ("Šubat-Enlil", "Šub", "Assyria", "SZE")
    TARBISU = ("Tarbiṣu", "Tar", "Assyria", "SKH")
    BABYLONIA = ("Babylonia", "Baba", None, None)
    ADAB = ("Adab", "Adb", "Babylonia", "ADB")
    BABYLON = ("Babylon", "Bab", "Babylonia", "BAB")
    BAD_TIBIRA = ("Bad-Tibira", "Btb", "Babylonia", "BTB")
    BORSIPPA = ("Borsippa", "Bor", "Babylonia", "BOR")
    CUTHA = ("Cutha", "Cut", "Babylonia", "GUD")
    DILBAT = ("Dilbat", "Dil", "Babylonia", "DLB")
    DIQDIQQAH = ("Diqdiqqah", "Diqd", "Babylonia", "DQD")
    DUR_KURIGALZU = ("Dūr-Kurigalzu", "Dku", "Babylonia", "AQA")
    ERIDU = ("Eridu", "Eri", "Babylonia", "ERI")
    ESNUNNA = ("Ešnunna", "Ešn", "Babylonia", "ESH")
    GARSANA = ("Garšana", "Gar", "Babylonia", "GRS")
    GIRSU = ("Girsu", "Gir", "Babylonia", "GIR")
    HURSAGKALAMA = ("Ḫursagkalama", "Hur", "Babylonia", None)
    IRISAGRIG = ("Irisagrig", "Irs", "Babylonia", "IRS")
    ISHAN_MIZIYAD = ("Ishān Miziyad", "Miz", "Babylonia", "MZA")
    ISIN = ("Isin", "Isn", "Babylonia", "ISN")
    ISHAN_HAFUDH = ("Ishān Hāfudh", "Haf", "Babylonia", "IHF")
    JAMDAT_NASR = ("Jamdat Naṣr", "Nasr", "Babylonia", "NSR")
    KISURRA = ("Kisurra", "Ksr", "Babylonia", "KSR")
    KIS = ("Kiš", "Kiš", "Babylonia", "KSH")
    KUTALLA = ("Kutalla", "Kut", "Babylonia", "SFR")
    LAGAS = ("Lagaš", "Lag", "Babylonia", "LAG")
    LARAK = ("Larak", "Lrk", "Babylonia", "LRK")
    LARSA = ("Larsa", "Lar", "Babylonia", "LAR")
    MALGIUM = ("Malgium", "Mal", "Babylonia", "TYA")
    MARAD = ("Marad", "Mrd", "Babylonia", "MRD")
    MASKAN_SAPIR = ("Maškan-šāpir", "Maš", "Babylonia", "MSK")
    METURAN = ("Meturan", "Met", "Babylonia", "HDD")
    TELL_AL_SIB = ("Meturan (Tell al-Sib)", "MetS", "Babylonia", "LSB")
    NEREBUN = ("Nērebtum", "Nēr", "Babylonia", "NRB")
    NIGIN = ("Nigin", "Nig", "Babylonia", "NGN")
    NIPPUR = ("Nippur", "Nip", "Babylonia", "NIP")
    PI_KASI = ("Pī-Kasî", "Pik", "Babylonia", "ANT")
    PUZRIS_DAGAN = ("Puzriš-Dagān", "Puz", "Babylonia", "DRE")
    SIPPAR = ("Sippar", "Sip", "Babylonia", "SAP")
    SIPPAR_AMNANUM = ("Sippar-Amnānum", "Sipam", "Babylonia", "SIP")
    SULAIYMAH = ("Sulaiymah", "Sul", "Babylonia", "HMR")
    SADUPPUM = ("Šaduppûm", "Šad", "Babylonia", "SDP")
    SAHRINU = ("Šaḫrīnu", "Šah", "Babylonia", None)
    SURUPPAK = ("Šuruppak", "Šur", "Babylonia", "SUR")
    TALL_ABU_SALABIKH = ("Tall Abū Ṣālabīkh", "Abs", "Babylonia", "ASK")
    TALL_AJRAB = ("Tall Ajrab", "Ajr", "Babylonia", "AGR")
    TALL_IMLIHIYAH = ("Tall Imlīḥiyah", "Iml", "Babylonia", "MLH")
    TALL_JIDAR = ("Tall Jidar", "Jid", "Babylonia", "JDR")
    TALL_KHAIBAR = ("Tall Khaibar", "Kha", "Babylonia", "KHA")
    TALL_AL_LAHAM = ("Tall al-Laḥam", "Lah", "Babylonia", "TLH")
    TALL_MUHAMAD = ("Tall Muḥamad", "Muh", "Babylonia", "TMH")
    TALL_AL_UBAID = ("Tall al-ʻUbaīd", "Ubd", "Babylonia", "UBD")
    TALL_UMM_AL_AJARIB = ("Tall Umm al-ʻAjarib", "Uaaj", "Babylonia", "UQR")
    TALL_UQAIR = ("Tall ʻUqair", "Uqa", "Babylonia", "UQA")
    TULUL_AL_BAQARAT = ("Tulūl al-Baqarāt", "Baq", "Babylonia", "TBA")
    TULUL_KHATAB = ("Tulūl Khaṭāb", "Khat", "Babylonia", "TKH")
    TUMMAL = ("Tummal", "Tum", "Babylonia", "DLH")
    TUTUB = ("Tutub", "Ttb", "Babylonia", "TTB")
    UMMA = ("Umma", "Umm", "Babylonia", "JOK")
    UMM_AL_HAFRIYAT = ("Umm al-Ḥafriyāt", "Hafr", "Babylonia", "UFR")
    UMM_AL_WAWIYA = ("Umm al-Wawiya", "Waw", "Babylonia", "UWW")
    UR = ("Ur", "Ur", "Babylonia", "URI")
    URUK = ("Uruk", "Urk", "Babylonia", "URU")
    YELKHI = ("Yelkhi", "Ylk", "Babylonia", "YEL")
    ZABALAM = ("Zabalam", "Zab", "Babylonia", "ZAB")
    ZARALULU = ("Zaralulu", "Zar", "Babylonia", "TDB")
    PERIPHERY = ("Periphery", "", None, None)
    ALALAKS = ("Alalakh", "Ala", "Periphery", "ALA")
    TELL_EL_AMARNA = ("Tell el-Amarna", "Ama", "Periphery", "AKH")
    ANAH = ("‘Anah", "Anh", "Periphery", "TNA")
    ANSAN = ("Anšan", "Anš", "Periphery", "ANS")
    BAKR_AWA = ("Bakr Āwā", "Bakr", "Periphery", "BAW")
    BARAH = ("Bārah", "Bar", "Periphery", "PRA")
    BITWATA = ("Bitwātā", "Bitw", "Periphery", "SNJ")
    DER = ("Dēr", "Der", "Periphery", "DER")
    DUGIRDKHAN = ("Dugirdkhan", "Dgr", "Periphery", "DGK")
    DUR_UNTAS = ("Dūr-Untaš", "Dun", "Periphery", "COZ")
    EBLA = ("Ebla", "Ebl", "Periphery", "EBA")
    ELAM = ("Elam", "Elam", "Periphery", None)
    EMAR = ("Emar", "Emr", "Periphery", "EMR")
    GLAYA = ("Glay‘a", "Gla", "Periphery", "GLA")
    HAMATH = ("Hamath", "Ham", "Periphery", "HAM")
    HATTUSA = ("Ḫattuša", "Hat", "Periphery", "HAT")
    KANES = ("Kaneš", "Kan", "Periphery", "KNS")
    KARKEMIS = ("Karkemiš", "Kar", "Periphery", "KRK")
    KIMUNAH = ("Kimūnah", "Kmn", "Periphery", "KMN")
    MARDAMAN = ("Mardaman", "Mard", "Periphery", "BAS")
    MARI = ("Mari", "Mar", "Periphery", "MAR")
    MEGIDDO = ("Megiddo", "Meg", "Periphery", "MGD")
    MILA_MERGI = ("Mila Mergi", "Milm", "Periphery", "MMG")
    NUZI = ("Nuzi", "Nuzi", "Periphery", "NUZ")
    PASIME = ("Pašime", "Paš", "Periphery", "PAS")
    PERSEPOLIS = ("Persepolis", "Per", "Periphery", "PRS")
    QATARA = ("Qatara", "Qat", "Periphery", "QAT")
    QATNA = ("Qaṭnā", "Qaṭ", "Periphery", "QTN")
    SUR_JARA = ("Sur Jar‘a", "Surj", "Periphery", "SJR")
    SUSA = ("Susa", "Sus", "Periphery", "SUS")
    SHISHIN = ("Shīshīn", "Shn", "Periphery", "SIN")
    SUSARRA = ("Šušarra", "Šuš", "Periphery", "SZU")
    TALL_BAZ_MUSIYAN = ("Tall Bāz Musiyān", "Bazm", "Periphery", "BZM")
    TALL_AL_FAKHAR = ("Tall al-Fakhar", "Fakh", "Periphery", "FAK")
    TALL_GHADAIYRIFAH = ("Tall Ghaḍaiyrīfah", "Ghad", "Periphery", "GDR")
    TALL_AL_HAWA = ("Tall al-Hawa", "Haw", "Periphery", "THW")
    TALL_IBRAHIM_BAYIS = ("Tall Ibrāhīm Bayis", "Iba", "Periphery", "IBA")
    TEPE_GOTVAND = ("Tepe Gotvand", "Tgo", "Periphery", "GTV")
    TERQA = ("Terqa", "Ter", "Periphery", "TRQ")
    TIKRIT = ("Tikrīt", "Tikr", "Periphery", "TIK")
    TUTTUL = ("Tuttul", "Ttl", "Periphery", "TUT")
    UGARIT = ("Ugarit", "Uga", "Periphery", "UGA")
    ZAWIYAH = ("Zawiyah", "Zaw", "Periphery", "ZWY")
    UNCERTAIN = ("Uncertain", "Unc", None, None)

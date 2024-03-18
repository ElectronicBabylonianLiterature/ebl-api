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
    DUR_KURIGALZU = ("Dūr-Kurigalzu", "Dku", "Babylonia", "AQA")
    ERIDU = ("Eridu", "Eri", "Babylonia", "ERI")
    ESNUNNA = ("Ešnunna", "Ešn", "Babylonia", "ESH")
    GARSANA = ("Garšana", "Gar", "Babylonia", "GRS")
    GIRSU = ("Girsu", "Gir", "Babylonia", "GIR")
    HURSAGKALAMA = ("Ḫursagkalama", "Hur", "Babylonia", None)
    IRISAGRIG = ("Irisagrig", "Irs", "Babylonia", "IRS")
    ISIN = ("Isin", "Isn", "Babylonia", "ISN")
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
    NEREBUN = ("Nērebtum", "Nēr", "Babylonia", "NRB")
    NIGIN = ("Nigin", "Nig", "Babylonia", "NGN")
    NIPPUR = ("Nippur", "Nip", "Babylonia", "NIP")
    PI_KASI = ("Pī-Kasî", "Pik", "Babylonia", "ANT")
    PUZRIS_DAGAN = ("Puzriš-Dagān", "Puz", "Babylonia", "DRE")
    SIPPAR = ("Sippar", "Sip", "Babylonia", "SAP")
    SIPPAR_AMNANUM = ("Sippar-Amnānum", "Sipam", "Babylonia", "SIP")
    SADUPPUM = ("Šaduppûm", "Šad", "Babylonia", "SDP")
    SAHRINU = ("Šaḫrīnu", "Šah", "Babylonia", None)
    SURUPPAK = ("Šuruppak", "Šur", "Babylonia", "SUR")
    TELL_AL_SIB = ("Meturan (Tell al-Sib)", "MetS", "Babylonia", "LSB")
    TUTUB = ("Tutub", "Ttb", "Babylonia", "TTB")
    UMMA = ("Umma", "Umm", "Babylonia", "JOK")
    UR = ("Ur", "Ur", "Babylonia", "URI")
    URUK = ("Uruk", "Urk", "Babylonia", "URU")
    ZABALAM = ("Zabalam", "Zab", "Babylonia", "ZAB")
    PERIPHERY = ("Periphery", "", None, None)
    ALALAKS = ("Alalakh", "Ala", "Periphery", "ALA")
    TELL_EL_AMARNA = ("Tell el-Amarna", "Ama", "Periphery", "AKH")
    ANSAN = ("Anšan", "Anš", "Periphery", "ANS")
    DER = ("Dēr", "Der", "Periphery", "DER")
    DUR_UNTAS = ("Dūr-Untaš", "Dun", "Periphery", "COZ")
    EBLA = ("Ebla", "Ebl", "Periphery", "EBA")
    ELAM = ("Elam", "Elam", "Periphery", None)
    EMAR = ("Emar", "Emr", "Periphery", "EMR")
    HAMATH = ("Hamath", "Ham", "Periphery", "HAM")
    HATTUSA = ("Ḫattuša", "Hat", "Periphery", "HAT")
    KANES = ("Kaneš", "Kan", "Periphery", "KNS")
    KARKEMIS = ("Karkemiš", "Kar", "Periphery", "KRK")
    MARI = ("Mari", "Mar", "Periphery", "MAR")
    MEGIDDO = ("Megiddo", "Meg", "Periphery", "MGD")
    PASIME = ("Pašime", "Paš", "Periphery", "PAS")
    PERSEPOLIS = ("Persepolis", "Per", "Periphery", "PRS")
    QATNA = ("Qaṭnā", "Qaṭ", "Periphery", "QTN")
    SUSA = ("Susa", "Sus", "Periphery", "SUS")
    TEPE_GOTVAND = ("Tepe Gotvand", "Tgo", "Periphery", "GTV")
    TERQA = ("Terqa", "Ter", "Periphery", "TRQ")
    TUTTUL = ("Tuttul", "Ttl", "Periphery", "TUT")
    UGARIT = ("Ugarit", "Uga", "Periphery", "UGA")
    UNCERTAIN = ("Uncertain", "Unc", None, None)
    SUR_JARA = ("Sur Jar‘a", "Surj", "Periphery", "SJR")
    KIMUNAH = ("Kimūnah", "Kmn", "Periphery", "KMN")
    TALL_UQAIR = ("Tall ʻUqair", "Uqa", "Babylonia", "UQA")
    ISHAN_MIZIYAD = ("Ishān Miziyad", "Miz", "Babylonia", "MZA")
    SULAIYMAH = ("Sulaiymah", "Sul", "Babylonia", "HMR")
    DUGIRDKHAN = ("Dugirdkhan", "Dgr", "Periphery", "DGK")
    MARDAMAN = ("Mardaman", "Mard", "Periphery", "BAS")
    TULUL_AL_BAQARAT = ("Tulūl al-Baqarāt", "Baq", "Babylonia", "TBA")
    YELKHI = ("Yelkhi", "Ylk", "Babylonia", "YEL")
    TALL_AL_UBAID = ("Tall al-ʻUbaīd", "Ubd", "Babylonia", "UBD")
    TALL_AL_HAWA = ("Tall al-Hawa", "Haw", "Periphery", "THW")
    TALL_GHADAIYRIFAH = ("Tall Ghaḍaiyrīfah", "Ghad", "Periphery", "GDR")
    DIQDIQQAH = ("Diqdiqqah", "Diqd", "Babylonia", "DQD")
    UMM_AL_WAWIYA = ("Umm al-Wawiya", "Waw", "Babylonia", "UWW")
    BITWATA = ("Bitwātā", "Bitw", "Periphery", "SNJ")
    TALL_JIDAR = ("Tall Jidar", "Jid", "Babylonia", "JDR")
    ISHAN_HAFUDH = ("Ishān Hāfudh", "Haf", "Babylonia", "IHF")
    UMM_AL_HAFRIYAT = ("Umm al-Ḥafriyāt", "Hafr", "Babylonia", "UFR")
    TALL_AL_LAHAM = ("Tall al-Laḥam", "Lah", "Babylonia", "TLH")
    TALL_BAZ_MUSIYAN = ("Tall Bāz Musiyān", "Bazm", "Periphery", "BZM")
    TALL_MUHAMAD = ("Tall Muḥamad", "Muh", "Babylonia", "TMH")
    TULUL_KHATAB = ("Tulūl Khaṭāb", "Khat", "Babylonia", "TKH")
    NUZI = ("Nuzi", "Nuzi", "Periphery", "NUZ")
    TALL_AJRAB = ("Tall Ajrab", "Ajr", "Babylonia", "AGR")
    QATARA = ("Qatara", "Qat", "Periphery", "QAT")
    TALL_UMM_AL_AJARIB = ("Tall Umm al-ʻAjarib", "Uaaj", "Babylonia", "UQR")
    SUSARRA = ("Šušarra", "Šuš", "Periphery", "SZU")
    SHISHIN = ("Shīshīn", "Shn", "Periphery", "SIN")
    TALL_ABU_SALABIKH = ("Tall Abū Ṣālabīkh", "Abs", "Babylonia", "ASK")
    TALL_IMLIHIYAH = ("Tall Imlīḥiyah", "Iml", "Babylonia", "MLH")
    TUMMAL = ("Tummal", "Tum", "Babylonia", "DLH")
    JAMDAT_NASR = ("Jamdat Naṣr", "Nasr", "Babylonia", "NSR")
    TALL_IBRAHIM_BAYIS = ("Tall Ibrāhīm Bayis", "Iba", "Periphery", "IBA")
    BARAH = ("Bārah", "Bar", "Periphery", "PRA")
    TIKRIT = ("Tikrīt", "Tikr", "Periphery", "TIK")
    ZAWIYAH = ("Zawiyah", "Zaw", "Periphery", "ZWY")
    ANAH = ("‘Anah", "Anh", "Periphery", "TNA")
    GLAYA = ("Glay‘a", "Gla", "Periphery", "GLA")
    ZARALULU = ("Zaralulu", "Zar", "Babylonia", "TDB")
    TALL_AL_FAKHAR = ("Tall al-Fakhar", "Fakh", "Periphery", "FAK")
    BAKR_AWA = ("Bakr Āwā", "Bakr", "Periphery", "BAW")
    MILA_MERGI = ("Mila Mergi", "Milm", "Periphery", "MMG")
    TALL_KHAIBAR = ("Tall Khaibar", "Kha", "Babylonia", "KHA")

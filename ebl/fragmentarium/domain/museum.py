from enum import Enum


class Museum(Enum):
    def __init__(self, museum_name, city="", country="", url=""):
        self.museum_name = museum_name
        self.city = city
        self.country = country
        self.url = url

    ANCIENT_CULTURES_CHICAGO = (
        "Institute for the Study of Ancient Cultures, West Asia & North Africa",
        "Chicago",
        "US",
        "https://isac.uchicago.edu/",
    )
    ASHMOLEAN_MUSEUM = ("Ashmolean Museum", "Oxford", "GB", "https://ashmolean.org/")
    AUSTRALIAN_INSTITUTE_OF_ARCHAEOLOGY = (
        "Australian Institute of Archaeology",
        "Melbourne",
        "AU",
        "https://www.aiarch.org.au/",
    )
    BANQUE_NATIONALE_DE_BELGIQUE = (
        "Banque Nationale de Belgique",
        "Brussels",
        "BE",
        "https://www.nbb.be/",
    )
    CHESTER_BEATTY_LIBRARY = (
        "Chester Beatty Library",
        "Dublin",
        "IE",
        "https://chesterbeatty.ie/",
    )
    COUVENT_SAINTE_ANNE = (
        "Couvent Sainte-Anne",
        "Jerusalem",
        "IL",
        "https://ste-anne-jerusalem.org/",
    )
    COUVENT_SAINT_ETIENNE = (
        "Couvent Saint-Étienne",
        "Jerusalem",
        "IL",
        "https://www.ebaf.edu/couvent/",
    )
    DE_LIAGRE_BOEHL_COLLECTION = (
        "de Liagre Böhl Collection",
        "Leiden",
        "NL",
        "https://www.nino-leiden.nl/collections/de-liagre-bohl-collection",
    )
    ECOLE_PRATIQUE_DES_HAUTES_ETUDES = (
        "École pratique des hautes Études",
        "Paris",
        "FR",
        "https://www.ephe.psl.eu/",
    )
    HARVARD_MUSEUM = (
        "Harvard Museum of the Ancient Near East",
        "Cambridge",
        "US",
        "https://hmane.harvard.edu/",
    )
    HARVARD_ART_MUSEUMS = (
        "Harvard Art Museums",
        "Cambridge",
        "US",
        "https://harvardartmuseums.org/",
    )
    HATAY_ARCHAEOLOGY_MUSEUM = (
        "Hatay Archaeology Museum",
        "Antakya",
        "TR",
        "https://muze.gov.tr/muze-detay?SectionId=HTY01&DistId=HTY",
    )
    HEARST_MUSEUM = (
        "Phoebe A. Hearst Museum of Anthropology",
        "Berkeley",
        "US",
        "https://hearstmuseum.berkeley.edu/",
    )
    HERMITAGE = (
        "The State Hermitage Museum",
        "Saint Petersburg",
        "RU",
        "https://www.hermitagemuseum.org/",
    )
    HILPRECHT_COLLECTION = (
        "Frau Professor Hilprecht Collection of Babylonian Antiquities",
        "Jena",
        "DE",
        "https://www.gw.uni-jena.de/fakultaet/institut-fuer-orientalistik-indogermanistik-ur-und-fruehgeschichtliche-archaeologie/altorientalistik/hilprecht-sammlung",
    )
    ISTANBUL_ARKEOLOJI_MUSEUM = (
        "İstanbul Arkeoloji Müzeleri",
        "Istanbul",
        "TR",
        "https://muze.gov.tr/muze-detay?SectionId=IAR01&DistId=IAR",
    )
    IZIKO_MUSEUMS_OF_SOUTH_AFRICA = (
        "Iziko Museums of South Africa",
        "Cape Town",
        "ZA",
        "https://www.iziko.org.za/",
    )
    KELSEY_MUSEUM = (
        "Kelsey Museum of Archaeology",
        "Ann Arbor",
        "US",
        "https://lsa.umich.edu/kelsey",
    )
    KUNSTHISTORISCHES_MUSEUM = (
        "Kunsthistorisches Museum",
        "Vienna",
        "AT",
        "https://www.khm.at/",
    )
    LOUVRE = ("Louvre", "Paris", "FR", "https://www.louvre.fr/")
    MOSUL_MUSEUM = (
        "Mosul Museum",
        "Mosul",
        "IQ",
        "https://www.wmf.org/monuments/mosul-cultural-museum",
    )
    MUSEE_D_ART = (
        "Musée d’Art et d’Histoire",
        "Geneva",
        "CH",
        "https://www.mahmah.ch/",
    )
    MUSEES_ROYAUX = (
        "Musées royaux d’Art et d’Histoire",
        "Brussels",
        "BE",
        "https://www.kmkg-mrah.be/",
    )
    MUSEUM_OF_ARCHAEOLOGY_AND_ANTHROPOLOGY_CAMBRIDGE = (
        "Museum of Archaeology and Anthropology",
        "Cambridge",
        "GB",
        "https://collections.maa.cam.ac.uk",
    )
    MUSEUM_OF_MONTSERRAT = (
        "Museum of Montserrat",
        "Montserrat",
        "ES",
        "https://www.museudemontserrat.com/en/index.html",
    )
    MUSEUM_OF_ANATOLIAN_CIVILIZATIONS = (
        "Anadolu Medeniyetleri Müzesi",
        "Ankara",
        "TR",
        "https://muze.gov.tr/muze-detay?SectionId=AMM01&DistId=AMM",
    )
    NATIONALMUSEET = ("Nationalmuseet", "Copenhagen", "DK", "https://en.natmus.dk/")
    OAKLAND_MUSEUM = (
        "Oakland Museum of California",
        "Oakland",
        "US",
        "https://museumca.org/",
    )
    PENN_MUSEUM = (
        "University of Pennsylvania Museum of Archaeology and Anthropology",
        "Philadelphia",
        "US",
        "https://www.penn.museum/",
    )
    MUETTER_MUSEUM = (
        "The Mütter Museum at The College of Physicians of Philadelphia",
        "Philadelphia",
        "US",
        "https://muttermuseum.org/",
    )
    PIERPONT_MORGAN = (
        "Pierpont Morgan Library & Museum",
        "New York",
        "US",
        "https://www.themorgan.org/",
    )
    PONTIFICAL_BIBLICAL_INSTITUTE = (
        "Pontifical Biblical Institute",
        "Rome",
        "IT",
        "http://www.biblico.it/",
    )
    PRIVATE_COLLECTION_CHICAGO = (
        "Private collection in Chicago",
        "Chicago",
        "US",
    )
    PRIVATE_COLLECTION_OF_J_CARRE = (
        "Private collection of J. Carré",
        "Brussels",
        "BE",
    )
    PRIVATE_COLLECTION_OF_M_FOEKEN = (
        "Private collection of M. Foeken",
        "Leiden",
        "NL",
    )
    PRIVATE_COLLECTION_OF_W_LAMPLOUGH = (
        "Private collection of W. Lamplough",
        "",
        "GB",
    )
    MCGILL_UNIVERSITY = (
        "McGill University Ethnological Collections",
        "Montreal",
        "CA",
        "https://www.mcgill.ca/redpath/collections/ethnology",
    )
    ROSICRUCIAN_EGYPTIAN_MUSEUM = (
        "Rosicrucian Egyptian Museum",
        "San Jose",
        "US",
        "https://egyptianmuseum.org/",
    )
    ROYAL_ONTARIO_MUSEUM = (
        "Royal Ontario Museum",
        "Toronto",
        "CA",
        "https://www.rom.on.ca/",
    )
    RYLANDS_INSTITUTE = (
        "John Rylands Research Institute and Library",
        "Manchester",
        "GB",
        "https://www.library.manchester.ac.uk/rylands/",
    )
    SANLIURFA_MUSEUM = (
        "Şanlıurfa Arkeoloji Müzesi",
        "Şanlıurfa",
        "TR",
        "https://muze.gov.tr/muze-detay?SectionId=SUM02&DistId=SUM",
    )
    SCHOYEN_COLLECTION = (
        "Schøyen Collection",
        "Oslo",
        "NO",
        "https://www.schoyencollection.com/",
    )
    SEPHARDIC_MUSEUM_OF_TOLEDO = (
        "Sephardic Museum of Toledo",
        "Toledo",
        "ES",
        "https://www.cultura.gob.es/msefardi/",
    )
    SLEMANI_MUSEUM = (
        "Slemani Museum",
        "Sulaymaniyah",
        "IQ",
        "https://slemanimuseum.org/",
    )
    THE_BRITISH_MUSEUM = (
        "The British Museum",
        "London",
        "GB",
        "https://www.britishmuseum.org/",
    )
    THE_FIELD_MUSEUM_OF_NATURAL_HISTORY = (
        "The Field Museum of Natural History",
        "Chicago",
        "US",
        "https://www.fieldmuseum.org/",
    )
    THE_FREE_LIBRARY_OF_PHILADELPHIA = (
        "The Free Library of Philadelphia",
        "Philadelphia",
        "US",
        "https://www.freelibrary.org/",
    )
    THE_IRAQ_MUSEUM = (
        "The Iraq Museum",
        "Baghdad",
        "IQ",
        "https://theiraqmuseum.com/",
    )
    THE_METROPOLITAN_MUSEUM_OF_ART = (
        "The Metropolitan Museum of Art",
        "New York",
        "US",
        "https://www.metmuseum.org/",
    )
    THE_WALTERS_ART_MUSEUM = (
        "The Walters Art Museum",
        "Baltimore",
        "US",
        "https://thewalters.org/",
    )
    TOPKAPI_SARAYI = (
        "Topkapı Sarayı Müzesi",
        "Istanbul",
        "TR",
        "https://muze.gen.tr/muze-detay/topkapi",
    )
    TRINITY_COLLEGE_DUBLIN = (
        "Trinity College Dublin",
        "Dublin",
        "IE",
        "https://www.tcd.ie/",
    )
    TURIN_DEPARTMENT_ARCHAEOLOGY = (
        "Sezione di Archeologia del Dipartimento di Studi Storici, Università di Torino",
        "Turin",
        "IT",
        "https://www.dipstudistorici.unito.it/",
    )
    URUK_WARKA_SAMMLUNG = (
        "Uruk-Warka-Sammlung",
        "Heidelberg",
        "DE",
        "https://www.ori.uni-heidelberg.de/assyriologie/institut/sammlungen/sa-uw.html",
    )
    VATICAN_MUSEUMS = (
        "Vatican Museums",
        "Vatican City",
        "VA",
        "http://www.museivaticani.va/",
    )
    VORDERASIATISCHES_MUSEUM = (
        "Vorderasiatisches Museum",
        "Berlin",
        "DE",
        "https://www.smb.museum/en/museums-institutions/vorderasiatisches-museum/home/",
    )
    YALE_PEABODY_COLLECTION = (
        "Yale Peabody Museum, Yale Babylonian Collection",
        "New Haven",
        "US",
        "https://peabody.yale.edu/explore/collections/yale-babylonian-collection",
    )
    UNKNOWN = ("UNKNOWN",)
    HYPERURANION = ("HYPERURANION",)

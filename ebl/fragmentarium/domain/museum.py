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
        "USA",
        "https://isac.uchicago.edu/",
    )
    ASHMOLEAN_MUSEUM = ("Ashmolean Museum", "Oxford", "GBR", "https://ashmolean.org/")
    AUSTRALIAN_INSTITUTE_OF_ARCHAEOLOGY = (
        "Australian Institute of Archaeology",
        "Melbourne",
        "AUS",
        "https://www.aiarch.org.au/",
    )
    CHESTER_BEATTY_LIBRARY = (
        "Chester Beatty Library",
        "Dublin",
        "IRL",
        "https://chesterbeatty.ie/",
    )
    COUVENT_SAINT_ETIENNE = (
        "Couvent Saint-Étienne",
        "Jerusalem",
        "ISR",
        "https://www.ebaf.edu/couvent/",
    )
    DE_LIAGRE_BOEHL_COLLECTION = (
        "de Liagre Böhl Collection",
        "Leiden",
        "NLD",
        "https://www.nino-leiden.nl/collections/de-liagre-bohl-collection",
    )
    ECOLE_PRATIQUE_DES_HAUTES_ETUDES = (
        "École pratique des hautes Études",
        "Paris",
        "FRA",
        "https://www.ephe.psl.eu/",
    )
    HATAY_ARCHAEOLOGY_MUSEUM = (
        "Hatay Archaeology Museum",
        "Antakya",
        "TUR",
        "https://muze.gov.tr/muze-detay?SectionId=HTY01&DistId=HTY",
    )
    HEARST_MUSEUM = (
        "Phoebe A. Hearst Museum of Anthropology",
        "Berkeley",
        "USA",
        "https://hearstmuseum.berkeley.edu/",
    )
    HILPRECHT_COLLECTION = (
        "Frau Professor Hilprecht Collection of Babylonian Antiquities",
        "Jena",
        "DEU",
        "https://www.gw.uni-jena.de/fakultaet/institut-fuer-orientalistik-indogermanistik-ur-und-fruehgeschichtliche-archaeologie/altorientalistik/hilprecht-sammlung",
    )
    ISTANBUL_ARKEOLOJI_MUSEUM = (
        "İstanbul Arkeoloji Müzeleri",
        "Istanbul",
        "TUR",
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
        "USA",
        "https://lsa.umich.edu/kelsey",
    )
    KUNSTHISTORISCHES_MUSEUM = (
        "Kunsthistorisches Museum",
        "Vienna",
        "AUT",
        "https://www.khm.at/",
    )
    LOUVRE = ("Louvre", "Paris", "FRA", "https://www.louvre.fr/")
    MUSEE_D_ART = (
        "Musée d’Art et d’Histoire",
        "Geneva",
        "CHE",
        "https://www.mahmah.ch/",
    )
    MUSEES_ROYAUX = (
        "Musées royaux d’Art et d’Histoire",
        "Brussels",
        "BEL",
        "https://www.kmkg-mrah.be/",
    )
    MUSEUM_OF_ARCHAEOLOGY_AND_ANTHROPOLOGY_CAMBRIDGE = (
        "Museum of Archaeology and Anthropology",
        "Cambridge",
        "GBR",
        "https://collections.maa.cam.ac.uk",
    )
    MUSEUM_OF_MONTSERRAT = (
        "Museum of Montserrat",
        "Montserrat",
        "ESP",
        "https://www.museudemontserrat.com/en/index.html",
    )
    MUSEUM_OF_ANATOLIAN_CIVILIZATIONS = (
        "Anadolu Medeniyetleri Müzesi",
        "Ankara",
        "TUR",
        "https://muze.gov.tr/muze-detay?SectionId=AMM01&DistId=AMM",
    )
    NATIONALMUSEET = ("Nationalmuseet", "Copenhagen", "DNK", "https://en.natmus.dk/")
    OAKLAND_MUSEUM = (
        "Oakland Museum of California",
        "Oakland",
        "USA",
        "https://museumca.org/",
    )
    PENN_MUSEUM = (
        "University of Pennsylvania Museum of Archaeology and Anthropology",
        "Philadelphia",
        "USA",
        "https://www.penn.museum/",
    )
    MUETTER_MUSEUM = (
        "The Mütter Museum at The College of Physicians of Philadelphia",
        "Philadelphia",
        "USA",
        "https://muttermuseum.org/",
    )
    PIERPONT_MORGAN = (
        "Pierpont Morgan Library & Museum",
        "New York",
        "USA",
        "https://www.themorgan.org/",
    )
    PONTIFICAL_BIBLICAL_INSTITUTE = (
        "Pontifical Biblical Institute",
        "Rome",
        "ITA",
        "http://www.biblico.it/",
    )
    PRIVATE_COLLECTION_CHICAGO = (
        "Private collection in Chicago",
        "Chicago",
        "USA",
    )
    PRIVATE_COLLECTION_OF_J_CARRE = (
        "Private collection of J. Carré",
        "Brussels",
        "BEL",
    )
    PRIVATE_COLLECTION_OF_M_FOEKEN = (
        "Private collection of M. Foeken",
        "Leiden",
        "NLD",
    )
    PRIVATE_COLLECTION_OF_W_LAMPLOUGH = (
        "Private collection of W. Lamplough",
        "",
        "GBR",
    )
    MCGILL_UNIVERSITY = (
        "McGill University Ethnological Collections",
        "Montreal",
        "CAN",
        "https://www.mcgill.ca/redpath/collections/ethnology",
    )
    ROSICRUCIAN_EGYPTIAN_MUSEUM = (
        "Rosicrucian Egyptian Museum",
        "San Jose",
        "USA",
        "https://egyptianmuseum.org/",
    )
    RYLANDS_INSTITUTE = (
        "John Rylands Research Institute and Library",
        "Manchester",
        "GRB",
        "https://www.library.manchester.ac.uk/rylands/",
    )
    SANLIURFA_MUSEUM = (
        "Şanlıurfa Arkeoloji Müzesi",
        "Şanlıurfa",
        "TUR",
        "https://muze.gov.tr/muze-detay?SectionId=SUM02&DistId=SUM",
    )
    THE_BRITISH_MUSEUM = (
        "The British Museum",
        "London",
        "GBR",
        "https://www.britishmuseum.org/",
    )
    THE_FIELD_MUSEUM_OF_NATURAL_HISTORY = (
        "The Field Museum of Natural History",
        "Chicago",
        "USA",
        "https://www.fieldmuseum.org/",
    )
    THE_FREE_LIBRARY_OF_PHILADELPHIA = (
        "The Free Library of Philadelphia",
        "Philadelphia",
        "USA",
        "https://www.freelibrary.org/",
    )
    THE_IRAQ_MUSEUM = (
        "The Iraq Museum",
        "Baghdad",
        "IRQ",
        "https://theiraqmuseum.com/",
    )
    THE_METROPOLITAN_MUSEUM_OF_ART = (
        "The Metropolitan Museum of Art",
        "New York",
        "USA",
        "https://www.metmuseum.org/",
    )
    THE_WALTERS_ART_MUSEUM = (
        "The Walters Art Museum",
        "Baltimore",
        "USA",
        "https://thewalters.org/",
    )
    TOPKAPI_SARAYI = (
        "Topkapı Sarayı Müzesi",
        "Istanbul",
        "TUR",
        "https://muze.gen.tr/muze-detay/topkapi"
    )
    TRINITY_COLLEGE_DUBLIN = (
        "Trinity College Dublin",
        "Dublin",
        "IRL",
        "https://www.tcd.ie/",
    )
    TURIN_DEPARTMENT_ARCHAEOLOGY = (
        "Sezione di Archeologia del Dipartimento di Studi Storici, Università di Torino",
        "Turin",
        "ITA",
        "https://www.dipstudistorici.unito.it/",
    )
    URUK_WARKA_SAMMLUNG = (
        "Uruk-Warka-Sammlung",
        "Heidelberg",
        "DEU",
        "https://www.ori.uni-heidelberg.de/assyriologie/institut/sammlungen/sa-uw.html",
    )
    VATICAN_MUSEUMS = (
        "Vatican Museums",
        "Vatican City",
        "VAT",
        "http://www.museivaticani.va/",
    )
    VORDERASIATISCHES_MUSEUM = (
        "Vorderasiatisches Museum",
        "Berlin",
        "DEU",
        "https://www.smb.museum/en/museums-institutions/vorderasiatisches-museum/home/",
    )
    YALE_PEABODY_COLLECTION = (
        "Yale Peabody Museum, Yale Babylonian Collection",
        "New Haven",
        "USA",
        "https://peabody.yale.edu/explore/collections/yale-babylonian-collection",
    )
    UNKNOWN = ("UNKNOWN",)
    HYPERURANION = ("HYPERURANION",)

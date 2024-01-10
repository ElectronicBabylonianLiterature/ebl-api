from enum import Enum


class Museum(Enum):
    def __init__(self, museum_name, city, country, url):
        self.museum_name = museum_name
        self.city = city
        self.country = country
        self.url = url

    ISTANBUL_ARKEOLOJI_MUSEUM = (
        "İstanbul Arkeoloji Müzeleri",
        "Istanbul",
        "TUR",
        "https://muze.gov.tr/muze-detay?SectionId=IAR01&DistId=IAR",
    )
    THE_IRAQ_MUSEUM = (
        "The Iraq Museum",
        "Baghdad",
        "IRQ",
        "https://theiraqmuseum.com/",
    )
    PENN_MUSEUM = (
        "University of Pennsylvania Museum of Archaeology and Anthropology",
        "Philadelphia",
        "USA",
        "https://www.penn.museum/",
    )
    ASHMOLEAN_MUSEUM = ("Ashmolean Museum", "Oxford", "GBR", "https://ashmolean.org/")
    PHYSICIANS_COLLEGE_PHILADELPHIA = (
        "College of Physicians of Philadelphia",
        "Philadelphia",
        "USA",
        "https://www.collegeofphysicians.org/",
    )
    COUVENT_SAINT_ETIENNE = (
        "Couvent Saint-Étienne",
        "Jerusalem",
        "ISR",
        "https://www.ebaf.edu/couvent/",
    )
    REDPATH_MUSEUM = (
        "Redpath Museum Ethnological Collections",
        "Montreal",
        "CAN",
        "https://www.mcgill.ca/redpath/collections/ethnology",
    )
    HILPRECHT_COLLECTION = (
        "Frau Professor Hilprecht Collection of Babylonian Antiquities",
        "Jena",
        "DEU",
        "https://www.gw.uni-jena.de/fakultaet/institut-fuer-orientalistik-indogermanistik-ur-und-fruehgeschichtliche-archaeologie/altorientalistik/hilprecht-sammlung",
    )
    HEARST_MUSEUM = (
        "Phoebe A. Hearst Museum of Anthropology",
        "Berkeley",
        "USA",
        "https://hearstmuseum.berkeley.edu/",
    )
    RYLANDS_INSTITUTE = (
        "John Rylands Research Institute and Library",
        "Manchester",
        "GRB",
        "https://www.library.manchester.ac.uk/rylands/",
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
    NATIONALMUSEET = ("Nationalmuseet", "Copenhagen", "DNK", "https://en.natmus.dk/")
    OAKLAND_MUSEUM = (
        "Oakland Museum of California",
        "Oakland",
        "USA",
        "https://museumca.org/",
    )
    ANCIENT_CULTURES_CHICAGO = (
        "Institute for the Study of Ancient Cultures, West Asia & North Africa",
        "Chicago",
        "USA",
        "https://isac.uchicago.edu/",
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
    ROSICRUCIAN_EGYPTIAN_MUSEUM = (
        "Rosicrucian Egyptian Museum",
        "San Jose",
        "USA",
        "https://egyptianmuseum.org/",
    )
    THE_BRITISH_MUSEUM = (
        "The British Museum",
        "London",
        "GBR",
        "https://www.britishmuseum.org/",
    )
    TRINITY_COLLEGE_DUBLIN = (
        "Trinity College Dublin",
        "Dublin",
        "IRL",
        "https://www.tcd.ie/",
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
    THE_WALTERS_ART_MUSEUM = (
        "The Walters Art Museum",
        "Baltimore",
        "USA",
        "https://thewalters.org/",
    )
    YALE_PEABODY_COLLECTION = (
        "Yale Peabody Museum, Yale Babylonian Collection",
        "New Haven",
        "USA",
        "https://peabody.yale.edu/explore/collections/yale-babylonian-collection",
    )
    ECOLE_PRATIQUE_DES_HAUTES_ETUDES = (
        "École pratique des hautes Études",
        "Paris",
        "FRA",
        "https://www.ephe.psl.eu/",
    )
    UNKNOWN = ("", "", "", "")

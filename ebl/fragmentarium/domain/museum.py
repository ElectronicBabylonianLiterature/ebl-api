from enum import Enum

class Museum(Enum):
    def __init__(self, museum_name, city, country, url):
        self.museum_name = museum_name
        self.city = city
        self.country = country
        self.url = url

    ISTANBUL_ARKEOLOJI_MUSEUM = ("İstanbul Arkeoloji Müzeleri", "Istanbul", "TUR", "https://muze.gov.tr/muze-detay?SectionId=IAR01&DistId=IAR")    
    THE_IRAQ_MUSEUM = ("The Iraq Museum", "Baghdad", "IRQ", "https://theiraqmuseum.com/")
    UNIVERSITY_OF_PENNSYLVANIA_MUSEUM_OF_ARCHAEOLOGY_AND_ANTHROPOLOGY = ("University of Pennsylvania Museum of Archaeology and Anthropology", "Philadelphia", "USA", "https://www.penn.museum/")
    ASHMOLEAN_MUSEUM = ("Ashmolean Museum", "Oxford", "GBR", "https://ashmolean.org/")
    COLLEGE_OF_PHYSICIANS_OF_PHILADELPHIA = ("College of Physicians of Philadelphia", "Philadelphia", "USA", "https://www.collegeofphysicians.org/")
    COUVENT_SAINT_ETIENNE = ("Couvent Saint-Étienne", "Jerusalem", "ISR", "https://www.ebaf.edu/couvent/")
    REDPATH_MUSEUM_ENTNOLOGICAL_COLLECTIONS = ("Redpath Museum Ethnological Collections", "Montreal", "CAN", "https://www.mcgill.ca/redpath/collections/ethnology")
    FRAU_PROFESSOR_HILPRECHT_COLLECTION_OF_BABYLONIAN_ANTIQUITIES = ("Frau Professor Hilprecht Collection of Babylonian Antiquities", "Jena", "DEU", "https://www.gw.uni-jena.de/fakultaet/institut-fuer-orientalistik-indogermanistik-ur-und-fruehgeschichtliche-archaeologie/altorientalistik/hilprecht-sammlung")
    PHOEBE_A_HEARST_MUSEUM_OF_ANTHROPOLOGY = ("Phoebe A. Hearst Museum of Anthropology", "Berkeley", "USA", "https://hearstmuseum.berkeley.edu/")
    JOHN_RYLANDS_RESEARCH_INSTITUTE_AND_LIBRARY = ("John Rylands Research Institute and Library", "Manchester", "GRB", "https://www.library.manchester.ac.uk/rylands/")
    KELSEY_MUSEUM_OF_ARCHAEOLOGY = ("Kelsey Museum of Archaeology", "Ann Arbor", "USA", "https://lsa.umich.edu/kelsey")
    KUNSTHISTORISCHES_MUSEUM = ("Kunsthistorisches Museum", "Vienna", "AUT", "https://www.khm.at/")
    LOUVRE = ("Louvre", "Paris", "FRA", "https://www.louvre.fr/")
    MUSEE_D_ART_ET_D_HISTOIRE = ("Musée d’Art et d’Histoire", "Geneva", "CHE", "https://www.mahmah.ch/")
    MUSEES_ROYAUX_D_ART_ET_D_HISTOIRE = ("Musées royaux d’Art et d’Histoire", "Brussels", "BEL", "https://www.kmkg-mrah.be/")
    NATIONALMUSEET = ("Nationalmuseet", "Copenhagen", "DNK", "https://en.natmus.dk/")
    OAKLAND_MUSEUM_OF_CALIFORNIA = ("Oakland Museum of California", "Oakland", "USA", "https://museumca.org/")
    INSTITUTE_FOR_THE_STUDY_OF_ANCIENT_CULTURES_WEST_ASIA_AND_NORTH_AFRICA = ("Institute for the Study of Ancient Cultures, West Asia & North Africa", "Chicago", "USA", "https://isac.uchicago.edu/")
    PIERPONT_MORGAN_LIBRARY_AND_MUSEUM = ("Pierpont Morgan Library & Museum", "New York", "USA", "https://www.themorgan.org/")
    PONTIFICAL_BIBLICAL_INSTITUTE = ("Pontifical Biblical Institute", "Rome", "ITA", "http://www.biblico.it/")
    ROSICRUCIAN_EGYPTIAN_MUSEUM = ("Rosicrucian Egyptian Museum", "San Jose", "USA", "https://egyptianmuseum.org/")
    THE_BRITISH_MUSEUM = ("The British Museum", "London", "GBR", "https://www.britishmuseum.org/")
    TRINITY_COLLEGE_DUBLIN = ("Trinity College Dublin", "Dublin", "IRL", "https://www.tcd.ie/")
    VATICAN_MUSEUMS = ("Vatican Museums", "Vatican City", "VAT", "http://www.museivaticani.va/")
    VORDERASIATISCHES_MUSEUM = ("Vorderasiatisches Museum", "Berlin", "DEU", "https://www.smb.museum/en/museums-institutions/vorderasiatisches-museum/home/")
    THE_WALTERS_ART_MUSEUM = ("The Walters Art Museum", "Baltimore", "USA", "https://thewalters.org/")
    YALE_PEABODY_MUSEUM_YALE_BABYLONIAN_COLLECTION = ("Yale Peabody Museum, Yale Babylonian Collection", "New Haven", "USA", "https://peabody.yale.edu/explore/collections/yale-babylonian-collection")
    ECOLE_PRATIQUE_DES_HAUTES_ETUDES = ("École pratique des hautes Études", "Paris", "FRA", "https://www.ephe.psl.eu/")
    UNKNOWN = ("Unknown", "Unknown", "Unknown", "Unknown")
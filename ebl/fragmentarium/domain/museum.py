from enum import Enum

from ebl.fragmentarium.domain import museum_entries_a_l
from ebl.fragmentarium.domain import museum_entries_m_s
from ebl.fragmentarium.domain import museum_entries_t_y


class Museum(Enum):
    def __init__(
        self,
        museum_name: str,
        city: str = "",
        country: str = "",
        url: str = "",
    ) -> None:
        self.museum_name = museum_name
        self.city = city
        self.country = country
        self.url = url

    ABBEY_MUSEUM = museum_entries_a_l.ABBEY_MUSEUM
    ADANA_ARKEOLOJI_MUZESI = museum_entries_a_l.ADANA_ARKEOLOJI_MUZESI
    ANCIENT_CULTURES_CHICAGO = museum_entries_a_l.ANCIENT_CULTURES_CHICAGO
    ASHMOLEAN_MUSEUM = museum_entries_a_l.ASHMOLEAN_MUSEUM
    AUSTRALIAN_INSTITUTE_OF_ARCHAEOLOGY = (
        museum_entries_a_l.AUSTRALIAN_INSTITUTE_OF_ARCHAEOLOGY
    )
    BATMAN_HASANKEYF_MUZESI = museum_entries_a_l.BATMAN_HASANKEYF_MUZESI
    BANQUE_NATIONALE_DE_BELGIQUE = museum_entries_a_l.BANQUE_NATIONALE_DE_BELGIQUE
    BRYN_MAWR_COLLEGE = museum_entries_a_l.BRYN_MAWR_COLLEGE
    CHESTER_BEATTY_LIBRARY = museum_entries_a_l.CHESTER_BEATTY_LIBRARY
    COLUMBIA_UNIVERSITY = museum_entries_a_l.COLUMBIA_UNIVERSITY
    COUVENT_SAINTE_ANNE = museum_entries_a_l.COUVENT_SAINTE_ANNE
    COUVENT_SAINT_ETIENNE = museum_entries_a_l.COUVENT_SAINT_ETIENNE
    DE_LIAGRE_BOEHL_COLLECTION = museum_entries_a_l.DE_LIAGRE_BOEHL_COLLECTION
    ECOLE_PRATIQUE_DES_HAUTES_ETUDES = (
        museum_entries_a_l.ECOLE_PRATIQUE_DES_HAUTES_ETUDES
    )
    HARVARD_MUSEUM = museum_entries_a_l.HARVARD_MUSEUM
    HARVARD_ART_MUSEUMS = museum_entries_a_l.HARVARD_ART_MUSEUMS
    HARVEY_CUSHING_WHITNEY_MEDICAL_LIBRARY = (
        museum_entries_a_l.HARVEY_CUSHING_WHITNEY_MEDICAL_LIBRARY
    )
    HATAY_ARCHAEOLOGY_MUSEUM = museum_entries_a_l.HATAY_ARCHAEOLOGY_MUSEUM
    HEARST_MUSEUM = museum_entries_a_l.HEARST_MUSEUM
    HERMITAGE = museum_entries_a_l.HERMITAGE
    HILPRECHT_COLLECTION = museum_entries_a_l.HILPRECHT_COLLECTION
    ISTANBUL_ARKEOLOJI_MUSEUM = museum_entries_a_l.ISTANBUL_ARKEOLOJI_MUSEUM
    IZIKO_MUSEUMS_OF_SOUTH_AFRICA = museum_entries_a_l.IZIKO_MUSEUMS_OF_SOUTH_AFRICA
    KATZ_CENTER = museum_entries_a_l.KATZ_CENTER
    KAYSERI_ARKEOLOJI_MUZESI = museum_entries_a_l.KAYSERI_ARKEOLOJI_MUZESI
    KELSEY_MUSEUM = museum_entries_a_l.KELSEY_MUSEUM
    KUNSTHISTORISCHES_MUSEUM = museum_entries_a_l.KUNSTHISTORISCHES_MUSEUM
    LOUVRE = museum_entries_a_l.LOUVRE
    MARDIN_MUZESI = museum_entries_m_s.MARDIN_MUZESI
    MOSUL_MUSEUM = museum_entries_m_s.MOSUL_MUSEUM
    MUSEE_D_ART = museum_entries_m_s.MUSEE_D_ART
    MUSEES_ROYAUX = museum_entries_m_s.MUSEES_ROYAUX
    MUSEUM_OF_ARCHAEOLOGY_AND_ANTHROPOLOGY_CAMBRIDGE = (
        museum_entries_m_s.MUSEUM_OF_ARCHAEOLOGY_AND_ANTHROPOLOGY_CAMBRIDGE
    )
    MUSEUM_OF_MONTSERRAT = museum_entries_m_s.MUSEUM_OF_MONTSERRAT
    MUSEUM_OF_ANATOLIAN_CIVILIZATIONS = (
        museum_entries_m_s.MUSEUM_OF_ANATOLIAN_CIVILIZATIONS
    )
    NATIONALMUSEET = museum_entries_m_s.NATIONALMUSEET
    MUSEO_NAZIONALE_D_ARTE_ORIENTALE = (
        museum_entries_m_s.MUSEO_NAZIONALE_D_ARTE_ORIENTALE
    )
    NATIONAL_MUSEUM_OF_WORLD_WRITING_SYSTEMS = (
        museum_entries_m_s.NATIONAL_MUSEUM_OF_WORLD_WRITING_SYSTEMS
    )
    OAKLAND_MUSEUM = museum_entries_m_s.OAKLAND_MUSEUM
    PENN_MUSEUM = museum_entries_m_s.PENN_MUSEUM
    MUETTER_MUSEUM = museum_entries_m_s.MUETTER_MUSEUM
    PIERPONT_MORGAN = museum_entries_m_s.PIERPONT_MORGAN
    PONTIFICAL_BIBLICAL_INSTITUTE = museum_entries_m_s.PONTIFICAL_BIBLICAL_INSTITUTE
    PRIVATE_COLLECTION_CHICAGO = museum_entries_m_s.PRIVATE_COLLECTION_CHICAGO
    PRIVATE_COLLECTION_OF_J_CARRE = museum_entries_m_s.PRIVATE_COLLECTION_OF_J_CARRE
    PRIVATE_COLLECTION_OF_M_FOEKEN = museum_entries_m_s.PRIVATE_COLLECTION_OF_M_FOEKEN
    PRIVATE_COLLECTION_OF_W_LAMPLOUGH = (
        museum_entries_m_s.PRIVATE_COLLECTION_OF_W_LAMPLOUGH
    )
    PRIVATE_COLLECTION_OF_Z_YILDIZ = museum_entries_m_s.PRIVATE_COLLECTION_OF_Z_YILDIZ
    MCGILL_UNIVERSITY = museum_entries_m_s.MCGILL_UNIVERSITY
    ROSICRUCIAN_EGYPTIAN_MUSEUM = museum_entries_m_s.ROSICRUCIAN_EGYPTIAN_MUSEUM
    ROYAL_ONTARIO_MUSEUM = museum_entries_m_s.ROYAL_ONTARIO_MUSEUM
    RYLANDS_INSTITUTE = museum_entries_m_s.RYLANDS_INSTITUTE
    SANLIURFA_MUSEUM = museum_entries_m_s.SANLIURFA_MUSEUM
    SCHOYEN_COLLECTION = museum_entries_m_s.SCHOYEN_COLLECTION
    SEPHARDIC_MUSEUM_OF_TOLEDO = museum_entries_m_s.SEPHARDIC_MUSEUM_OF_TOLEDO
    SLEMANI_MUSEUM = museum_entries_m_s.SLEMANI_MUSEUM
    SPURLOCK_MUSEUM = museum_entries_m_s.SPURLOCK_MUSEUM
    THE_BRITISH_MUSEUM = museum_entries_t_y.THE_BRITISH_MUSEUM
    THE_FIELD_MUSEUM_OF_NATURAL_HISTORY = (
        museum_entries_t_y.THE_FIELD_MUSEUM_OF_NATURAL_HISTORY
    )
    THE_FREE_LIBRARY_OF_PHILADELPHIA = (
        museum_entries_t_y.THE_FREE_LIBRARY_OF_PHILADELPHIA
    )
    THE_IRAQ_MUSEUM = museum_entries_t_y.THE_IRAQ_MUSEUM
    THE_METROPOLITAN_MUSEUM_OF_ART = museum_entries_t_y.THE_METROPOLITAN_MUSEUM_OF_ART
    THE_WALTERS_ART_MUSEUM = museum_entries_t_y.THE_WALTERS_ART_MUSEUM
    TOPKAPI_SARAYI = museum_entries_t_y.TOPKAPI_SARAYI
    TRINITY_COLLEGE_DUBLIN = museum_entries_t_y.TRINITY_COLLEGE_DUBLIN
    TURIN_DEPARTMENT_ARCHAEOLOGY = museum_entries_t_y.TURIN_DEPARTMENT_ARCHAEOLOGY
    URUK_WARKA_SAMMLUNG = museum_entries_t_y.URUK_WARKA_SAMMLUNG
    VATICAN_MUSEUMS = museum_entries_t_y.VATICAN_MUSEUMS
    VORDERASIATISCHES_MUSEUM = museum_entries_t_y.VORDERASIATISCHES_MUSEUM
    YALE_PEABODY_COLLECTION = museum_entries_t_y.YALE_PEABODY_COLLECTION
    UNKNOWN = ("UNKNOWN",)
    HYPERURANION = ("HYPERURANION",)

from ebl.atf.atf import Atf
from ebl.fragment.transliteration_update import TransliterationUpdate


class TransliterationUpdateFactory:
    def __init__(self, transliteration_search_service):
        self._transliteration_search_service = transliteration_search_service

    def create(self, atf: Atf, notes: str = ''):
        signs = self._transliteration_search_service.convert_atf_to_signs(atf)
        return TransliterationUpdate(atf, notes, signs)

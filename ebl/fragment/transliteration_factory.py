from ebl.fragment.transliteration import Transliteration
from ebl.text.atf import Atf


class TransliterationFactory:
    def __init__(self, transliteration_search_service):
        self._transliteration_search_service = transliteration_search_service

    def create(self, atf: Atf, notes: str = ''):
        signs = self._transliteration_search_service.convert_atf_to_signs(atf)
        return Transliteration(atf, notes, signs)

from ebl.fragment.transliteration import Transliteration
from ebl.text.atf import Atf
from ebl.transliteration_search.clean_atf import CleanAtf


class TransliterationFactory:
    def __init__(self, transliteration_search_service):
        self._transliteration_search_service = transliteration_search_service

    def create(self, atf: Atf, notes: str = ''):
        signs = CleanAtf(atf).to_signs(self._transliteration_search_service)
        return Transliteration(atf, notes, signs)

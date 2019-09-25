from ebl.atf.atf import Atf
from ebl.fragmentarium.application.transliteration_update import \
    TransliterationUpdate
from ebl.transliteration_search.application.transliteration_search import \
    TransliterationSearch


class TransliterationUpdateFactory:
    def __init__(self, transliteration_search: TransliterationSearch):
        self._transliteration_search = transliteration_search

    def create(self, atf: Atf, notes: str = ''):
        signs = self._transliteration_search.convert_atf_to_signs(atf)
        return TransliterationUpdate(atf, notes, signs)

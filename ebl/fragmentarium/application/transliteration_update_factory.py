from ebl.atf.atf import Atf
from ebl.fragmentarium.application.transliteration_update import \
    TransliterationUpdate
from ebl.transliteration_search.application.atf_converter import \
    AtfConverter


class TransliterationUpdateFactory:
    def __init__(self, transliteration_search: AtfConverter):
        self._transliteration_search = transliteration_search

    def create(self, atf: Atf, notes: str = ''):
        signs = self._transliteration_search.convert_atf_to_signs(atf)
        return TransliterationUpdate(atf, notes, signs)

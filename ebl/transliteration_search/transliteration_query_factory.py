from ebl.text.atf import Atf
from ebl.transliteration_search.clean_atf import CleanAtf
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery


class TransliterationQueryFactory:
    def __init__(self, transliteration_search):
        self._transliteration_search = transliteration_search

    def create(self, atf: Atf):
        values = CleanAtf(atf).values
        signs = self._transliteration_search.map_readings(values)
        return TransliterationQuery(signs)

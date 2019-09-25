from ebl.atf.atf import Atf
from ebl.atf.clean_atf import CleanAtf
from ebl.transliteration_search.application.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.application.transliteration_search import \
    TransliterationSearch


class TransliterationQueryFactory:
    def __init__(self, transliteration_search: TransliterationSearch):
        self._transliteration_search = transliteration_search

    def create(self, atf: Atf):
        values = CleanAtf(atf).values
        signs = self._transliteration_search.convert_values_to_signs(values)
        return TransliterationQuery(signs)

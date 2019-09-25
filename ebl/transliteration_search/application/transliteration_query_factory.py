from ebl.atf.atf import Atf
from ebl.transliteration_search.application.atf_converter import \
    AtfConverter
from ebl.transliteration_search.application.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.domain.clean_atf import CleanAtf


class TransliterationQueryFactory:
    def __init__(self, transliteration_search: AtfConverter):
        self._transliteration_search = transliteration_search

    def create(self, atf: Atf):
        values = CleanAtf(atf).values
        signs = self._transliteration_search.convert_values_to_signs(values)
        return TransliterationQuery(signs)

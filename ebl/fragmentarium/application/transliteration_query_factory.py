from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.atf_converter import AtfConverter
from ebl.transliteration.domain.atf import Atf


class TransliterationQueryFactory:
    def __init__(self, atf_converter: AtfConverter):
        self._atf_converter = atf_converter

    def create(self, transliteration: Atf):
        signs = self._atf_converter.convert_atf_to_sign_matrix(transliteration)
        return TransliterationQuery(signs)

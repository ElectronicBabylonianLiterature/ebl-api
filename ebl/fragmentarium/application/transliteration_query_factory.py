from ebl.atf.domain.atf import Atf
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery
from ebl.signs.application.atf_converter import \
    AtfConverter


class TransliterationQueryFactory:
    def __init__(self, atf_converter: AtfConverter):
        self._atf_converter = atf_converter

    def create(self, atf: Atf):
        signs = self._atf_converter.convert_atf_to_sign_matrix(atf)
        return TransliterationQuery(signs)

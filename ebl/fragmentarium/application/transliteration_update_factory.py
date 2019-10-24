from ebl.fragmentarium.domain.transliteration_update import \
    TransliterationUpdate
from ebl.transliteration.application.atf_converter import AtfConverter
from ebl.transliteration.domain.atf import Atf


class TransliterationUpdateFactory:
    def __init__(self, atf_converter: AtfConverter):
        self._atf_converter = atf_converter

    def create(self, atf: Atf, notes: str = ''):
        signs = '\n'.join([
            ' '.join(row)
            for row in self._atf_converter.convert_atf_to_sign_matrix(atf)
        ])
        return TransliterationUpdate(atf, notes, signs)

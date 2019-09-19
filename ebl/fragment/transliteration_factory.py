from ebl.fragment.transliteration import Transliteration
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.text.atf import Atf


class TransliterationFactory:
    def __init__(self, sign_list):
        self._sign_list = sign_list

    def create(self, atf: Atf, notes: str = ''):
        return Transliteration(atf, notes).with_signs(self._sign_list)

    def create_query(self, atf: Atf):
        signs = self._sign_list.map_readings(Transliteration(atf).values)
        return TransliterationQuery(signs)

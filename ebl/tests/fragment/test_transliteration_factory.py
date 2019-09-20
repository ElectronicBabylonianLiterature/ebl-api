from ebl.fragment.transliteration import Transliteration
from ebl.fragment.transliteration_factory import TransliterationFactory
from ebl.text.atf import Atf


def test_create(transliteration_search, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    factory = TransliterationFactory(transliteration_search)
    atf = Atf('1. šu gid₂')
    notes = 'notes'

    assert factory.create(atf, notes) == Transliteration(atf, notes, 'ŠU BU')

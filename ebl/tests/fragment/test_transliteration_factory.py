from ebl.fragment.transliteration import Transliteration
from ebl.fragment.transliteration_factory import TransliterationFactory
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.text.atf import Atf


def test_create(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    factory = TransliterationFactory(sign_list)
    atf = Atf('1. šu gid₂')
    notes = 'notes'

    assert factory.create(atf, notes) == Transliteration(atf, notes, 'ŠU BU')


def test_create_query(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    factory = TransliterationFactory(sign_list)
    atf = Atf('1. šu\n2. gid₂')

    assert factory.create_query(atf) == TransliterationQuery([['ŠU'], ['BU']])

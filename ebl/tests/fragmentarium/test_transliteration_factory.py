from ebl.atf.domain.atf import Atf
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.domain.transliteration_update import \
    TransliterationUpdate


def test_create(transliteration_search, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    factory = TransliterationUpdateFactory(transliteration_search)
    atf = Atf('1. šu gid₂')
    notes = 'notes'

    assert factory.create(atf, notes) ==\
        TransliterationUpdate(atf, notes, 'ŠU BU')

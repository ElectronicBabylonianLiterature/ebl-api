from ebl.atf.domain.atf import Atf
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.domain.transliteration_update import \
    TransliterationUpdate


def test_create(atf_converter, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationUpdateFactory(atf_converter)
    atf = Atf('1. šu gid₂')
    notes = 'notes'

    assert factory.create(atf, notes) ==\
        TransliterationUpdate(atf, notes, 'ŠU BU')

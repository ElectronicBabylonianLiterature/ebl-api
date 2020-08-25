from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.atf import Atf


def test_create(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationUpdateFactory(sign_repository)
    atf = Atf("1. šu gid₂")
    notes = "notes"

    assert factory.create(atf, notes) == TransliterationUpdate(atf, notes, "ŠU BU")

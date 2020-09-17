import pytest  # pyre-ignore[21]
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.lark_parser import parse_atf_lark


def test_create(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    factory = TransliterationUpdateFactory(sign_repository)
    atf = Atf("1. šu gid₂")
    notes = "notes"

    assert factory.create(atf, notes) == TransliterationUpdate(
        parse_atf_lark(atf), notes, "ŠU BU"
    )


def test_create_empty(sign_repository):
    factory = TransliterationUpdateFactory(sign_repository)
    atf = Atf("")

    assert factory.create(atf, "") == TransliterationUpdate(parse_atf_lark(atf), "", "")


def test_create_invalid_atf(sign_repository):
    factory = TransliterationUpdateFactory(sign_repository)
    atf = Atf("1. {kur}?")

    with pytest.raises(
        TransliterationError, match="Invalid transliteration"
    ) as excinfo:
        factory.create(atf)

    assert excinfo.value.errors == [
        {
            "description": ("Invalid line:  {kur}?\n" "                    ^\n"),
            "lineNumber": 1,
        }
    ]

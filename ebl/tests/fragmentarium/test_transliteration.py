import pytest  # pyre-ignore

from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.transliteration_error import TransliterationError


def test_atf():
    atf = Atf("1. kur")
    transliteration = TransliterationUpdate(atf)

    assert transliteration.atf == atf


def test_text():
    text = parse_atf_lark("1. kur")
    transliteration = TransliterationUpdate(text=text)

    assert transliteration.text == text


def test_notes():
    notes = "notes"
    transliteration = TransliterationUpdate(notes=notes)

    assert transliteration.notes == notes


def test_signs():
    signs = "X"
    transliteration = TransliterationUpdate(signs=signs)

    assert transliteration.signs == signs


def test_validate_valid_signs(transliteration_factory):
    TransliterationUpdate(Atf("1. šu gid₂"), signs="ŠU BU")


def test_validate_invalid_value():
    with pytest.raises(
        TransliterationError, match="Invalid transliteration"
    ) as excinfo:
        TransliterationUpdate(Atf("1. invalid values"), signs="? ?")

    assert excinfo.value.errors == [{"description": "Invalid value", "lineNumber": 1}]


def test_validate_multiple_errors():
    with pytest.raises(
        TransliterationError, match="Invalid transliteration"
    ) as excinfo:
        TransliterationUpdate(
            Atf("1. invalid values\n$ (valid)\n2. more invalid values"),
            signs="? ?\n? ? ?",
        )

    assert excinfo.value.errors == [
        {"description": "Invalid value", "lineNumber": 1},
        {"description": "Invalid value", "lineNumber": 3},
    ]

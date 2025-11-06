import pytest

from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.transliteration_error import TransliterationError


def test_text():
    text = parse_atf_lark("1. kur")
    transliteration = TransliterationUpdate(text)

    assert transliteration.text == text


def test_signs():
    signs = "X"
    transliteration = TransliterationUpdate(signs=signs)

    assert transliteration.signs == signs


def test_validate_valid_signs(transliteration_factory):
    TransliterationUpdate(parse_atf_lark("1. šu gid₂"), signs="ŠU BU")


def test_validate_invalid_value():
    with pytest.raises(
        TransliterationError, match="Invalid transliteration"
    ) as excinfo:
        TransliterationUpdate(parse_atf_lark("1. x"), signs="? ?")

    assert excinfo.value.errors == [{"description": "Invalid value", "lineNumber": 1}]


def test_validate_multiple_errors():
    with pytest.raises(
        TransliterationError, match="Invalid transliteration"
    ) as excinfo:
        TransliterationUpdate(
            parse_atf_lark("1. x\n$ (valid)\n2. x"), signs="? ?\n? ? ?"
        )

    assert excinfo.value.errors == [
        {"description": "Invalid value", "lineNumber": 1},
        {"description": "Invalid value", "lineNumber": 3},
    ]

import pytest

from ebl.fragment.transliteration import Transliteration
from ebl.fragment.validator import Validator
from ebl.text.atf import Atf
from ebl.text.transliteration_error import TransliterationError


def test_validate_empty():
    transliteration = Transliteration(Atf(''))
    Validator(transliteration).validate()


def test_validate_valid_no_signs():
    transliteration = Transliteration(Atf('1. value'))
    Validator(transliteration).validate()


def test_validate_valid_signs(transliteration_factory, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    transliteration = Transliteration(Atf('1. šu gid₂'), signs='ŠU BU')
    Validator(transliteration).validate()


def test_validate_invalid_atf():
    transliteration = Transliteration(Atf('$ this is not valid'))

    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Validator(transliteration).validate()

    assert excinfo.value.errors == [
        {
            'description': 'Invalid line',
            'lineNumber': 1
        }
    ]


def test_validate_invalid_value(sign_list):
    transliteration = Transliteration(Atf('1. invalid values'), signs='? ?')

    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Validator(transliteration).validate()

    assert excinfo.value.errors == [
        {
            'description': 'Invalid value',
            'lineNumber': 1
        }
    ]


def test_validate_multiple_errors(sign_list):
    transliteration = Transliteration(
        Atf('1. invalid values\n$ not valid\n2. more invalid values'),
        signs='? ?\n? ? ?'
    )

    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Validator(transliteration).validate()

    assert excinfo.value.errors == [
        {
            'description': 'Invalid line',
            'lineNumber': 2
        },
        {
            'description': 'Invalid value',
            'lineNumber': 1
        },
        {
            'description': 'Invalid value',
            'lineNumber': 3
        }
    ]


def test_get_errors(sign_list):
    transliteration = Transliteration(
        Atf('1. invalid values\n$ not valid\n2. more invalid values'),
        signs='? ?\n? ? ?'
    )

    assert Validator(transliteration).get_errors() == [
        {
            'description': 'Invalid line',
            'lineNumber': 2
        },
        {
            'description': 'Invalid value',
            'lineNumber': 1
        },
        {
            'description': 'Invalid value',
            'lineNumber': 3
        }
    ]

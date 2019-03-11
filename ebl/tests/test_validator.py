import pytest
from ebl.fragment.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragmentarium.validator import Validator


def test_validate_empty():
    transliteration = Transliteration('')
    Validator(transliteration).validate()


def test_validate_valid_no_signs():
    transliteration = Transliteration('1. value')
    Validator(transliteration).validate()


def test_validate_valid_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    transliteration = Transliteration('1. šu gid₂').with_signs(sign_list)
    Validator(transliteration).validate()


def test_validate_invalid_atf():
    transliteration = Transliteration('$ this is not valid')

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
    transliteration =\
        Transliteration('1. invalid values').with_signs(sign_list)

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
        '1. invalid values\n$ not valid\n2. more invalid values'
    ).with_signs(sign_list)

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
        '1. invalid values\n$ not valid\n2. more invalid values'
    ).with_signs(sign_list)

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

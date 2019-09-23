import pytest

from ebl.fragment.transliteration import Transliteration
from ebl.text.atf import Atf
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text
from ebl.text.transliteration_error import TransliterationError


def test_atf():
    atf = Atf('1. kur')
    transliteration = Transliteration(atf)

    assert transliteration.atf == atf


def test_notes():
    notes = 'notes'
    transliteration = Transliteration(notes=notes)

    assert transliteration.notes == notes


def test_signs():
    signs = 'X'
    transliteration = Transliteration(signs=signs)

    assert transliteration.signs == signs


@pytest.mark.parametrize('transliteration,expected', [
    (Transliteration(), Text()),
    (Transliteration(Atf('1. kur')), parse_atf(Atf('1. kur')))
])
def test_parse(transliteration, expected):
    assert transliteration.parse() == expected


def test_parse_invalid():
    transliteration = Transliteration(Atf('1. ö invalid atf'))
    with pytest.raises(TransliterationError):
        transliteration.parse()


def test_validate_valid_signs(transliteration_factory, sign_list, signs):
    Transliteration(Atf('1. šu gid₂'), signs='ŠU BU')


def test_invalid_atf():
    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Transliteration(Atf('$ this is not valid'))

    assert excinfo.value.errors == [
        {
            'description': 'Invalid line',
            'lineNumber': 1
        }
    ]


def test_validate_invalid_value(sign_list):
    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Transliteration(Atf('1. invalid values'), signs='? ?')

    assert excinfo.value.errors == [
        {
            'description': 'Invalid value',
            'lineNumber': 1
        }
    ]


def test_validate_multiple_errors(sign_list):
    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        Transliteration(
            Atf('1. invalid values\n$ (valid)\n2. more invalid values'),
            signs='? ?\n? ? ?'
        )

    assert excinfo.value.errors == [
        {
            'description': 'Invalid value',
            'lineNumber': 1
        },
        {
            'description': 'Invalid value',
            'lineNumber': 3
        }
    ]

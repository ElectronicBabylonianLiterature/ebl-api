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
    with pytest.raises(TransliterationError):
        Transliteration(Atf('invalid atf')).parse()

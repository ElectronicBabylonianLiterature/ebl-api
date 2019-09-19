import pytest

from ebl.fragment.transliteration import Transliteration
from ebl.fragment.value import Grapheme, NotReading, Reading
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


def test_filtered():
    transliteration = Transliteration(
        Atf('&K11111\n@reverse\n\n$ end of side\n#note\n=: foo\n1. ku\n2. $AN')
    )
    assert transliteration.filtered == ['1. ku', '2. $AN']


def test_values():
    transliteration = Transliteration(Atf(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ end of side\n'
        '#note\n'
        '=: foo\n'
        '1. ku X x\n'
        '2. $AN |BI×IS|\n'
        '3. nuₓ'
    ))
    assert transliteration.values == [
        [Reading('ku', 1, '?'), NotReading('X'), NotReading('X')],
        [Reading('an', 1, '?'), Grapheme('|BI×IS|')],
        [NotReading('?')]
    ]


def test_with_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    transliteration = Transliteration(Atf('1. šu gid₂'))

    assert transliteration.with_signs(sign_list).signs == 'ŠU BU'


@pytest.mark.parametrize('transliteration,expected', [
    (Transliteration(), Text()),
    (Transliteration(Atf('1. kur')), parse_atf(Atf('1. kur')))
])
def test_parse(transliteration, expected):
    assert transliteration.parse() == expected


def test_parse_invalid():
    with pytest.raises(TransliterationError):
        Transliteration(Atf('invalid atf')).parse()

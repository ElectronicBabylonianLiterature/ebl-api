from ebl.fragment.transliteration import Transliteration
from ebl.fragment.value import NotReading, Reading


def test_atf():
    transliteration = Transliteration('transliteration', 'notes')

    assert transliteration.atf == 'transliteration'


def test_notes():
    transliteration = Transliteration('transliteration', 'notes')

    assert transliteration.notes == 'notes'


def test_filtered():
    transliteration = Transliteration(
        '&K11111\n@reverse\n\n$ end of side\n#note\n=: foo\n1. ku\n2. $AN'
    )
    assert transliteration.filtered == ['1. ku', '2. $AN']


def test_values():
    transliteration = Transliteration(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ end of side\n'
        '#note\n'
        '=: foo\n'
        '1. ku X x\n'
        '2. $AN |BI×IS|\n'
        '3. nuₓ'
    )
    assert transliteration.values == [
        [Reading('ku', 1, '?'), NotReading('X'), NotReading('X')],
        [Reading('an', 1, '?'), NotReading('|BI×IS|')],
        [NotReading('?')]
    ]


def test_with_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    transliteration = Transliteration('1. šu gid₂')

    assert transliteration.with_signs(sign_list).signs == 'ŠU BU'


def test_tokenize():
    transliteration = Transliteration(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ (end of side)\n'
        '#some notes\n'
        '=: foo\n'
        '1. [...] šu-gid₂ k[u ...]\n'
        '2. x X'
    )

    expected = [
        ['&K11111'],
        ['@reverse'],
        [''],
        ['$ (end of side)'],
        ['#some notes'],
        ['=: foo'],
        ['1.', '[...]', 'šu-gid₂', 'k[u', '...]'],
        ['2.', 'x', 'X']
    ]

    assert transliteration.tokenize(lambda value: value) == expected


def test_tokenize_empty():
    transliteration = Transliteration('')

    assert transliteration.tokenize(lambda value: value) == []

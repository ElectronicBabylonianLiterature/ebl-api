import pytest
from ebl.text.atf_parser import WORD
from ebl.text.token import Word


@pytest.mark.parametrize("atf,expected", [
    ('x', Word('x')),
    ('X', Word('X')),
    ('x#', Word('x#')),
    ('X#', Word('X#')),
    ('12', Word('12')),
    ('GAL', Word('GAL')),
    ('|GAL|', Word('|GAL|')),
    ('x-ti', Word('x-ti')),
    ('ti-X', Word('ti-X')),
    ('r]u-u₂-qu', Word('r]u-u₂-qu')),
    ('ru?-u₂-qu', Word('ru?-u₂-qu')),
    ('na-a[n-', Word('na-a[n-')),
    ('-ku]-nu', Word('-ku]-nu')),
    ('gid₂', Word('gid₂')),
    ('|U₄&KAM₂|', Word('|U₄&KAM₂|')),
    ('U]₄.14.KAM₂', Word('U]₄.14.KAM₂')),
    ('{ku}nu', Word('{ku}nu')),
    ('{{ku}}nu', Word('{{ku}}nu')),
    ('ku{{nu}}', Word('ku{{nu}}')),
    ('ku{nu}', Word('ku{nu}')),
    ('ku{nu}si', Word('ku{nu}si')),
    ('ku{{nu}}si', Word('ku{{nu}}si')),
    ('{iti}]ŠE', Word('{iti}]ŠE')),
    ('šu/|BI×IS|', Word('šu/|BI×IS|')),
    ('{kur}aš+šur', Word('{kur}aš+šur')),
    ('i-le-ʾe-[e]', Word('i-le-ʾe-[e]')),
    ('U₄.27/29.KAM', Word('U₄.27/29.KAM')),
    ('x/m[a', Word('x/m[a')),
    ('SAL.{+mu-ru-ub}[LA', Word('SAL.{+mu-ru-ub}[LA')),
    ('I.{d}[UTU?', Word('I.{d}[UTU?')),
    ('.x.KAM', Word('.x.KAM')),
    ('3.AM₃', Word('3.AM₃')),
    ('<{he-pi₂', Word('<{he-pi₂')),
    ('eš-šu₂}>', Word('eš-šu₂}>')),
    ('<{10}>', Word('<{10}>')),
    ('KA₂?].DINGIR.RA[{ki}?', Word('KA₂?].DINGIR.RA[{ki}?')),
    ('{ud]u}?', Word('{ud]u}?')),
    ('{d}?nu?-di]m₂?-mu[d?', Word('{d}?nu?-di]m₂?-mu[d?')),
    ('<GAR>?', Word('<GAR>?')),
    ('gam/:', Word('gam/:'))
])
def test_word(atf, expected):
    assert WORD.map(Word).parse(atf) == expected

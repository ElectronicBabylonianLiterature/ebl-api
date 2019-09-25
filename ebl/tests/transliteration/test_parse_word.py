import pytest

from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.text_parser import LONE_DETERMINATIVE, WORD
from ebl.transliteration.domain.token import LoneDeterminative, Word


@pytest.mark.parametrize('parser', [
    lambda atf: WORD.map(Word).parse(atf),
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
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
    ('i-le-ʾe-[e', Word('i-le-ʾe-[e')),
    ('U₄.27/29.KAM', Word('U₄.27/29.KAM')),
    ('x/m[a', Word('x/m[a')),
    ('SAL.{+mu-ru-ub}[LA', Word('SAL.{+mu-ru-ub}[LA')),
    ('I.{d}[UTU?', Word('I.{d}[UTU?')),
    ('.x.KAM', Word('.x.KAM')),
    ('3.AM₃', Word('3.AM₃')),
    ('<{10}>bu', Word('<{10}>bu')),
    ('KA₂?].DINGIR.RA[{ki?}', Word('KA₂?].DINGIR.RA[{ki?}')),
    ('{d?}nu?-di]m₂?-mu[d?', Word('{d?}nu?-di]m₂?-mu[d?')),
    ('<GAR?>', Word('<GAR?>')),
    ('gam/:', Word('gam/:')),
    ('lu₂@v', Word('lu₂@v')),
    ('{lu₂@v}UM.ME.[A', Word('{lu₂@v}UM.ME.[A')),
    ('{lu₂@v}]KAB.SAR-M[EŠ', Word('{lu₂@v}]KAB.SAR-M[EŠ')),
    ('MIN<(ta-ne₂-hi)>', Word('MIN<(ta-ne₂-hi)>')),
    ('UN#', Word('UN#')),
    ('he₂-<(pa₃)>', Word('he₂-<(pa₃)>')),
    ('{[i]ti}AB', Word('{[i]ti}AB')),
    ('in]-', Word('in]-')),
    ('<en-da-ab>', Word('<en-da-ab>')),
    ('me-e-li-°\\ku°', Word('me-e-li-°\\ku°')),
    ('°me-e-li\\°-ku', Word('°me-e-li\\°-ku')),
    ('me-°e\\li°-ku', Word('me-°e\\li°-ku')),
    ('me-°e\\li°-me-°e\\li°-ku', Word('me-°e\\li°-me-°e\\li°-ku')),
])
def test_word(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    lambda atf: LONE_DETERMINATIVE.map(LoneDeterminative).parse(atf),
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
    ('<{10}>', LoneDeterminative('<{10}>')),
    ('{ud]u?}', LoneDeterminative('{ud]u?}')),
    ('{u₂#}', LoneDeterminative('{u₂#}')),
    ('{lu₂@v}', LoneDeterminative('{lu₂@v}')),
    ('{k[i]}', LoneDeterminative('{k[i]}'))
])
def test_lone_determinative(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    LONE_DETERMINATIVE.parse,
    parse_word
])
@pytest.mark.parametrize('atf', [
    '{udu}?'
])
def test_invalid_lone_determinative(parser, atf):
    with pytest.raises(Exception):
        parser(atf)


@pytest.mark.parametrize('parser', [
    WORD.parse,
    parse_word
])
@pytest.mark.parametrize('atf', [
    'sal/: šim',
    '<GAR>?',
    'KA₂]?.DINGIR.RA[{ki?}',
    'KA₂?].DINGIR.RA[{ki}?',
    'k[a]?'
])
def test_invalid(parser, atf):
    with pytest.raises(Exception):
        parser(atf)

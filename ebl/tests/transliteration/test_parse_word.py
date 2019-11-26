import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.sign_tokens import UnidentifiedSign, \
    UnclearSign, Reading
from ebl.transliteration.domain.tokens import ValueToken, UnknownNumberOfSigns
from ebl.transliteration.domain.word_tokens import Word, LoneDeterminative, \
    Joiner, InWordNewline


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
    ('x', Word('x', parts=[UnclearSign()])),
    ('X', Word('X', parts=[UnidentifiedSign()])),
    ('x?', Word('x?', parts=[UnclearSign([atf.Flag.UNCERTAIN])])),
    ('X#', Word('X#', parts=[UnidentifiedSign([atf.Flag.DAMAGE])])),
    ('12', Word('12', parts=[Reading('12')])),
    ('du₁₁', Word('du₁₁', parts=[Reading('du', 11)])),
    ('GAL', Word('GAL', parts=[ValueToken('GAL')])),
    ('kur(GAL)', Word('kur(GAL)', parts=[Reading('kur', sign='GAL')])),
    ('|GAL|', Word('|GAL|', parts=[ValueToken('|GAL|')])),
    ('x-ti', Word('x-ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.HYPHEN), Reading('ti')
    ])),
    ('x.ti', Word('x.ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.DOT), Reading('ti')
    ])),
    ('x+ti', Word('x+ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.PLUS), Reading('ti')
    ])),
    ('x:ti', Word('x:ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.COLON), Reading('ti')
    ])),
    ('ti-X', Word('ti-X', parts=[
        Reading('ti'), Joiner(atf.Joiner.HYPHEN), UnidentifiedSign()
    ])),
    ('r]u-u₂-qu', Word('r]u-u₂-qu', parts=[
        Reading('r]u'), Joiner(atf.Joiner.HYPHEN), Reading('u', 2),
        Joiner(atf.Joiner.HYPHEN), Reading('qu')
    ])),
    ('ru?-u₂-qu', Word('ru?-u₂-qu', parts=[
        Reading('ru', flags=[atf.Flag.UNCERTAIN]), Joiner(atf.Joiner.HYPHEN),
        Reading('u', 2), Joiner(atf.Joiner.HYPHEN), Reading('qu')
    ])),
    ('na-a[n-', Word('na-a[n-', parts=[
        Reading('na'), Joiner(atf.Joiner.HYPHEN),
        Reading('a[n'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('-ku]-nu', Word('-ku]-nu', parts=[
        Joiner(atf.Joiner.HYPHEN), Reading('ku'), ValueToken(']'),
        Joiner(atf.Joiner.HYPHEN), Reading('nu')
    ])),
    ('gid₂', Word('gid₂', parts=[Reading('gid', 2)])),
    ('|U₄&KAM₂|', Word('|U₄&KAM₂|', parts=[ValueToken('|U₄&KAM₂|')])),
    ('U₄].14.KAM₂', Word('U₄].14.KAM₂', parts=[
        ValueToken('U₄'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        Reading('14'), Joiner(atf.Joiner.DOT), ValueToken('KAM₂')
    ])),
    ('{ku}nu', Word('{ku}nu', parts=[
        ValueToken('{'), Reading('ku'), ValueToken('}'), Reading('nu')
    ])),
    ('{{ku}}nu', Word('{{ku}}nu', parts=[
        ValueToken('{{'), Reading('ku'), ValueToken('}}'), Reading('nu')
    ])),
    ('ku{{nu}}', Word('ku{{nu}}', parts=[
        Reading('ku'), ValueToken('{{'), Reading('nu'), ValueToken('}}')
    ])),
    ('ku{nu}', Word('ku{nu}', parts=[
        Reading('ku'), ValueToken('{'), Reading('nu'), ValueToken('}')
    ])),
    ('ku{{nu}}si', Word('ku{{nu}}si', parts=[
        Reading('ku'), ValueToken('{{'), Reading('nu'), ValueToken('}}'),
        Reading('si')
    ])),
    ('{iti}]ŠE', Word('{iti}]ŠE', parts=[
        ValueToken('{'), Reading('iti'), ValueToken('}'), ValueToken(']'),
        ValueToken('ŠE')
    ])),
    ('šu/|BI×IS|', Word('šu/|BI×IS|', parts=[ValueToken('šu/|BI×IS|')])),
    ('{kur}aš+šur', Word('{kur}aš+šur', parts=[
        ValueToken('{'), Reading('kur'), ValueToken('}'), Reading('aš'),
        Joiner(atf.Joiner.PLUS), Reading('šur')
    ])),
    ('i-le-ʾe-[e', Word('i-le-ʾe-[e', parts=[
        Reading('i'), Joiner(atf.Joiner.HYPHEN), Reading('le'),
        Joiner(atf.Joiner.HYPHEN), Reading('ʾe'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('['), Reading('e')
    ])),
    ('U₄.27/29.KAM', Word('U₄.27/29.KAM', parts=[
        ValueToken('U₄'), Joiner(atf.Joiner.DOT), ValueToken('27/29'),
        Joiner(atf.Joiner.DOT), ValueToken('KAM')
    ])),
    ('x/m[a', Word('x/m[a', parts=[ValueToken('x/m[a')])),
    ('SAL.{+mu-ru-ub}', Word('SAL.{+mu-ru-ub}', parts=[
        ValueToken('SAL'), Joiner(atf.Joiner.DOT), ValueToken('{+'),
        Reading('mu'), Joiner(atf.Joiner.HYPHEN), Reading('ru'),
        Joiner(atf.Joiner.HYPHEN), Reading('ub'), ValueToken('}')
    ])),
    ('{+mu-ru-ub}[LA', Word('{+mu-ru-ub}[LA', parts=[
        ValueToken('{+'), Reading('mu'), Joiner(atf.Joiner.HYPHEN),
        Reading('ru'), Joiner(atf.Joiner.HYPHEN), Reading('ub'),
        ValueToken('}'), ValueToken('['), ValueToken('LA')
    ])),
    ('I.{d}', Word('I.{d}', parts=[
        ValueToken('I'), Joiner(atf.Joiner.DOT), ValueToken('{'),
        Reading('d'), ValueToken('}')
    ])),
    ('{d}[UTU?', Word('{d}[UTU?', parts=[
        ValueToken('{'), Reading('d'), ValueToken('}'), ValueToken('['),
        ValueToken('UTU?')
    ])),
    ('.x.KAM', Word('.x.KAM', parts=[
        Joiner(atf.Joiner.DOT), UnclearSign(), Joiner(atf.Joiner.DOT),
        ValueToken('KAM')
    ])),
    ('3.AM₃', Word('3.AM₃', parts=[
        Reading('3'), Joiner(atf.Joiner.DOT), ValueToken('AM₃')
    ])),
    ('<{10}>bu', Word('<{10}>bu', parts=[
        ValueToken('<'), ValueToken('{'), Reading('10'), ValueToken('}'),
        ValueToken('>'), Reading('bu')
    ])),
    ('KA₂?].DINGIR.RA[{ki?}', Word('KA₂?].DINGIR.RA[{ki?}', parts=[
        ValueToken('KA₂?'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        ValueToken('DINGIR'), Joiner(atf.Joiner.DOT), ValueToken('RA'),
        ValueToken('['), ValueToken('{'),
        Reading('ki', flags=[atf.Flag.UNCERTAIN]), ValueToken('}')
    ])),
    ('{d?}nu?-di]m₂?-mu[d?', Word('{d?}nu?-di]m₂?-mu[d?', parts=[
        ValueToken('{'), Reading('d', flags=[atf.Flag.UNCERTAIN]),
        ValueToken('}'), Reading('nu', flags=[atf.Flag.UNCERTAIN]),
        Joiner(atf.Joiner.HYPHEN),
        Reading('di]m', 2, flags=[atf.Flag.UNCERTAIN]),
        Joiner(atf.Joiner.HYPHEN),
        Reading('mu[d', flags=[atf.Flag.UNCERTAIN])
    ])),
    ('<GAR?>', Word('<GAR?>', parts=[
        ValueToken('<'), ValueToken('GAR?'), ValueToken('>')
    ])),
    ('lu₂@v', Word('lu₂@v', parts=[Reading('lu', 2, modifiers=['@v'])])),
    ('{lu₂@v}UM.ME.[A', Word('{lu₂@v}UM.ME.[A', parts=[
        ValueToken('{'), Reading('lu', 2, modifiers=['@v']), ValueToken('}'),
        ValueToken('UM'), Joiner(atf.Joiner.DOT), ValueToken('ME'),
        Joiner(atf.Joiner.DOT), ValueToken('['), ValueToken('A')
    ])),
    ('{lu₂@v}]KAB.SAR-M[EŠ', Word('{lu₂@v}]KAB.SAR-M[EŠ', parts=[
        ValueToken('{'), Reading('lu', 2, modifiers=['@v']), ValueToken('}'),
        ValueToken(']'), ValueToken('KAB'), Joiner(atf.Joiner.DOT),
        ValueToken('SAR'), Joiner(atf.Joiner.HYPHEN), ValueToken('M[EŠ')
    ])),
    ('MIN<(ta-ne₂-hi)>', Word('MIN<(ta-ne₂-hi)>', parts=[
        ValueToken('MIN<(ta-ne₂-hi)>')
    ])),
    ('UN#', Word('UN#', parts=[ValueToken('UN#')])),
    ('he₂-<(pa₃)>', Word('he₂-<(pa₃)>', parts=[
        Reading('he', 2), Joiner(atf.Joiner.HYPHEN), ValueToken('<('),
        Reading('pa', 3), ValueToken(')>')
    ])),
    ('{[i]ti}AB', Word('{[i]ti}AB', parts=[
        ValueToken('{'), ValueToken('['), Reading('i]ti'),
        ValueToken('}'), ValueToken('AB')
    ])),
    ('in]-', Word('in]-', parts=[
        Reading('in'), ValueToken(']'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('<en-da-ab>', Word('<en-da-ab>', parts=[
        ValueToken('<'), Reading('en'), Joiner(atf.Joiner.HYPHEN),
        Reading('da'), Joiner(atf.Joiner.HYPHEN), Reading('ab'),
        ValueToken('>')
    ])),
    ('me-e-li-°\\ku°', Word('me-e-li-°\\ku°', parts=[
        Reading('me'), Joiner(atf.Joiner.HYPHEN), Reading('e'),
        Joiner(atf.Joiner.HYPHEN), Reading('li'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), ValueToken('\\'), Reading('ku'), ValueToken('°')
    ])),
    ('°me-e-li\\°-ku', Word('°me-e-li\\°-ku', parts=[
        ValueToken('°'), Reading('me'), Joiner(atf.Joiner.HYPHEN),
        Reading('e'), Joiner(atf.Joiner.HYPHEN), Reading('li'),
        ValueToken('\\'), ValueToken('°'), Joiner(atf.Joiner.HYPHEN),
        Reading('ku')
    ])),
    ('me-°e\\li°-ku', Word('me-°e\\li°-ku', parts=[
        Reading('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        Reading('e'), ValueToken('\\'), Reading('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), Reading('ku')
    ])),
    ('me-°e\\li°-me-°e\\li°-ku', Word('me-°e\\li°-me-°e\\li°-ku', parts=[
        Reading('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        Reading('e'), ValueToken('\\'), Reading('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), Reading('me'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), Reading('e'), ValueToken('\\'), Reading('li'),
        ValueToken('°'), Joiner(atf.Joiner.HYPHEN), Reading('ku')
    ])),
    ('...{d}kur', Word('...{d}kur', parts=[
        UnknownNumberOfSigns(), ValueToken('{'), Reading('d'),
        ValueToken('}'), Reading('kur')
    ])),
    ('kur{d}...', Word('kur{d}...', parts=[
        Reading('kur'), ValueToken('{'), Reading('d'), ValueToken('}'),
        UnknownNumberOfSigns()
    ])),
    ('...-kur-...', Word('...-kur-...', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.HYPHEN), Reading('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns()
    ])),
    ('kur-...-kur-...-kur', Word('kur-...-kur-...-kur', parts=[
        Reading('kur'), Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), Reading('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), Reading('kur')
    ])),
    ('...]-ku', Word('...]-ku', parts=[
        UnknownNumberOfSigns(), ValueToken(']'), Joiner(atf.Joiner.HYPHEN),
        Reading('ku')
    ])),
    ('ku-[...', Word('ku-[...', parts=[
        Reading('ku'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
        UnknownNumberOfSigns()
    ])),
    ('....ku', Word('....ku', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.DOT), Reading('ku')
    ])),
    ('ku....', Word('ku....', parts=[
        Reading('ku'), Joiner(atf.Joiner.DOT), UnknownNumberOfSigns()
    ])),
    ('(x)]', Word('(x)]', parts=[
        ValueToken('('), UnclearSign(), ValueToken(')'), ValueToken(']')
    ])),
    ('[{d}UTU', Word('[{d}UTU', parts=[
        ValueToken('['), ValueToken('{'), Reading('d'), ValueToken('}'),
        ValueToken('UTU')
    ])),
    ('{m#}[{d}AG-sa-lim', Word('{m#}[{d}AG-sa-lim', parts=[
        ValueToken('{'), Reading('m', flags=[atf.Flag.DAMAGE]),
        ValueToken('}'), ValueToken('['), ValueToken('{'), Reading('d'),
        ValueToken('}'), ValueToken('AG'), Joiner(atf.Joiner.HYPHEN),
        Reading('sa'), Joiner(atf.Joiner.HYPHEN), Reading('lim')
    ])),
    ('ša#-[<(mu-un-u₅)>]', Word('ša#-[<(mu-un-u₅)>]', parts=[
        Reading('ša', flags=[atf.Flag.DAMAGE]), Joiner(atf.Joiner.HYPHEN),
        ValueToken('['), ValueToken('<('), Reading('mu'),
        Joiner(atf.Joiner.HYPHEN), Reading('un'), Joiner(atf.Joiner.HYPHEN),
        Reading('u', 5), ValueToken(')>'), ValueToken(']')
    ])),
    ('|UM×(ME.DA)|-b[i?', Word('|UM×(ME.DA)|-b[i?', parts=[
        ValueToken('|UM×(ME.DA)|'), Joiner(atf.Joiner.HYPHEN),
        Reading('b[i', flags=[atf.Flag.UNCERTAIN])
    ])),
    ('mu-un;-e₃', Word('mu-un;-e₃', parts=[
        Reading('mu'), Joiner(atf.Joiner.HYPHEN), Reading('un'),
        InWordNewline(), Joiner(atf.Joiner.HYPHEN), Reading('e', 3)
    ]))
])
def test_word(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
    ('<{10}>', LoneDeterminative('<{10}>', parts=[
        ValueToken('<'), ValueToken('{'),  Reading('10'), ValueToken('}'),
        ValueToken('>')
    ])),
    ('{ud]u?}', LoneDeterminative('{ud]u?}', parts=[
        ValueToken('{'), Reading('ud]u', flags=[atf.Flag.UNCERTAIN]),
        ValueToken('}')
    ])),
    ('{u₂#}', LoneDeterminative('{u₂#}', parts=[
        ValueToken('{'), Reading('u', 2, flags=[atf.Flag.DAMAGE]),
        ValueToken('}')
    ])),
    ('{lu₂@v}', LoneDeterminative('{lu₂@v}', parts=[
        ValueToken('{'), Reading('lu', 2, modifiers=['@v']), ValueToken('}')
    ])),
    ('{k[i]}', LoneDeterminative('{k[i]}', parts=[
        ValueToken('{'), Reading('k[i'), ValueToken(']'), ValueToken('}')
    ])),
    ('{[k]i}', LoneDeterminative('{[k]i}', parts=[
        ValueToken('{'), ValueToken('['), Reading('k]i'), ValueToken('}')
    ]))
])
def test_lone_determinative(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf', [
    '{udu}?'
])
def test_invalid_lone_determinative(parser, atf):
    with pytest.raises(UnexpectedInput):
        parser(atf)


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf', [
    'sal/: šim',
    '<GAR>?',
    'KA₂]?.DINGIR.RA[{ki?}',
    'KA₂?].DINGIR.RA[{ki}?',
    'k[a]?',
    ':-sal',
    'gam/:'
    '//sal',
    'Š[A₃?...]'
])
def test_invalid(parser, atf):
    with pytest.raises((UnexpectedInput, ParseError)):
        parser(atf)

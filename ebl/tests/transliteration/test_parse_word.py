import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.sign_tokens import UnidentifiedSign, \
    UnclearSign, Reading, Number
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
    ('12', Word('12', parts=[Number.of(12)])),
    ('du₁₁', Word('du₁₁', parts=[Reading.of('du', 11)])),
    ('GAL', Word('GAL', parts=[ValueToken('GAL')])),
    ('kur(GAL)', Word('kur(GAL)', parts=[Reading.of('kur', sign='GAL')])),
    ('|GAL|', Word('|GAL|', parts=[ValueToken('|GAL|')])),
    ('x-ti', Word('x-ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.HYPHEN), Reading.of('ti')
    ])),
    ('x.ti', Word('x.ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.DOT), Reading.of('ti')
    ])),
    ('x+ti', Word('x+ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.PLUS), Reading.of('ti')
    ])),
    ('x:ti', Word('x:ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.COLON), Reading.of('ti')
    ])),
    ('ti-X', Word('ti-X', parts=[
        Reading.of('ti'), Joiner(atf.Joiner.HYPHEN), UnidentifiedSign()
    ])),
    ('r]u-u₂-qu', Word('r]u-u₂-qu', parts=[
        Reading.of('r]u'), Joiner(atf.Joiner.HYPHEN), Reading.of('u', 2),
        Joiner(atf.Joiner.HYPHEN), Reading.of('qu')
    ])),
    ('ru?-u₂-qu', Word('ru?-u₂-qu', parts=[
        Reading.of('ru', flags=[atf.Flag.UNCERTAIN]),
        Joiner(atf.Joiner.HYPHEN), Reading.of('u', 2),
        Joiner(atf.Joiner.HYPHEN), Reading.of('qu')
    ])),
    ('na-a[n-', Word('na-a[n-', parts=[
        Reading.of('na'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('a[n'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('-ku]-nu', Word('-ku]-nu', parts=[
        Joiner(atf.Joiner.HYPHEN), Reading.of('ku'), ValueToken(']'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('nu')
    ])),
    ('gid₂', Word('gid₂', parts=[Reading.of('gid', 2)])),
    ('|U₄&KAM₂|', Word('|U₄&KAM₂|', parts=[ValueToken('|U₄&KAM₂|')])),
    ('U₄].14.KAM₂', Word('U₄].14.KAM₂', parts=[
        ValueToken('U₄'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        Number.of(14), Joiner(atf.Joiner.DOT), ValueToken('KAM₂')
    ])),
    ('{ku}nu', Word('{ku}nu', parts=[
        ValueToken('{'), Reading.of('ku'), ValueToken('}'), Reading.of('nu')
    ])),
    ('{{ku}}nu', Word('{{ku}}nu', parts=[
        ValueToken('{{'), Reading.of('ku'), ValueToken('}}'), Reading.of('nu')
    ])),
    ('ku{{nu}}', Word('ku{{nu}}', parts=[
        Reading.of('ku'), ValueToken('{{'), Reading.of('nu'), ValueToken('}}')
    ])),
    ('ku{nu}', Word('ku{nu}', parts=[
        Reading.of('ku'), ValueToken('{'), Reading.of('nu'), ValueToken('}')
    ])),
    ('ku{{nu}}si', Word('ku{{nu}}si', parts=[
        Reading.of('ku'), ValueToken('{{'), Reading.of('nu'), ValueToken('}}'),
        Reading.of('si')
    ])),
    ('{iti}]ŠE', Word('{iti}]ŠE', parts=[
        ValueToken('{'), Reading.of('iti'), ValueToken('}'), ValueToken(']'),
        ValueToken('ŠE')
    ])),
    ('šu/|BI×IS|', Word('šu/|BI×IS|', parts=[ValueToken('šu/|BI×IS|')])),
    ('{kur}aš+šur', Word('{kur}aš+šur', parts=[
        ValueToken('{'), Reading.of('kur'), ValueToken('}'), Reading.of('aš'),
        Joiner(atf.Joiner.PLUS), Reading.of('šur')
    ])),
    ('i-le-ʾe-[e', Word('i-le-ʾe-[e', parts=[
        Reading.of('i'), Joiner(atf.Joiner.HYPHEN), Reading.of('le'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('ʾe'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('['), Reading.of('e')
    ])),
    ('U₄.27/29.KAM', Word('U₄.27/29.KAM', parts=[
        ValueToken('U₄'), Joiner(atf.Joiner.DOT), ValueToken('27/29'),
        Joiner(atf.Joiner.DOT), ValueToken('KAM')
    ])),
    ('x/m[a', Word('x/m[a', parts=[ValueToken('x/m[a')])),
    ('SAL.{+mu-ru-ub}', Word('SAL.{+mu-ru-ub}', parts=[
        ValueToken('SAL'), Joiner(atf.Joiner.DOT), ValueToken('{+'),
        Reading.of('mu'), Joiner(atf.Joiner.HYPHEN), Reading.of('ru'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('ub'), ValueToken('}')
    ])),
    ('{+mu-ru-ub}[LA', Word('{+mu-ru-ub}[LA', parts=[
        ValueToken('{+'), Reading.of('mu'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('ru'), Joiner(atf.Joiner.HYPHEN), Reading.of('ub'),
        ValueToken('}'), ValueToken('['), ValueToken('LA')
    ])),
    ('I.{d}', Word('I.{d}', parts=[
        ValueToken('I'), Joiner(atf.Joiner.DOT), ValueToken('{'),
        Reading.of('d'), ValueToken('}')
    ])),
    ('{d}[UTU?', Word('{d}[UTU?', parts=[
        ValueToken('{'), Reading.of('d'), ValueToken('}'), ValueToken('['),
        ValueToken('UTU?')
    ])),
    ('.x.KAM', Word('.x.KAM', parts=[
        Joiner(atf.Joiner.DOT), UnclearSign(), Joiner(atf.Joiner.DOT),
        ValueToken('KAM')
    ])),
    ('3.AM₃', Word('3.AM₃', parts=[
        Number.of(3), Joiner(atf.Joiner.DOT), ValueToken('AM₃')
    ])),
    ('<{10}>bu', Word('<{10}>bu', parts=[
        ValueToken('<'), ValueToken('{'), Number.of(10), ValueToken('}'),
        ValueToken('>'), Reading.of('bu')
    ])),
    ('KA₂?].DINGIR.RA[{ki?}', Word('KA₂?].DINGIR.RA[{ki?}', parts=[
        ValueToken('KA₂?'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        ValueToken('DINGIR'), Joiner(atf.Joiner.DOT), ValueToken('RA'),
        ValueToken('['), ValueToken('{'),
        Reading.of('ki', flags=[atf.Flag.UNCERTAIN]), ValueToken('}')
    ])),
    ('{d?}nu?-di]m₂?-mu[d?', Word('{d?}nu?-di]m₂?-mu[d?', parts=[
        ValueToken('{'), Reading.of('d', flags=[atf.Flag.UNCERTAIN]),
        ValueToken('}'), Reading.of('nu', flags=[atf.Flag.UNCERTAIN]),
        Joiner(atf.Joiner.HYPHEN),
        Reading.of('di]m', 2, flags=[atf.Flag.UNCERTAIN]),
        Joiner(atf.Joiner.HYPHEN),
        Reading.of('mu[d', flags=[atf.Flag.UNCERTAIN])
    ])),
    ('<GAR?>', Word('<GAR?>', parts=[
        ValueToken('<'), ValueToken('GAR?'), ValueToken('>')
    ])),
    ('lu₂@v', Word('lu₂@v', parts=[Reading.of('lu', 2, modifiers=['@v'])])),
    ('{lu₂@v}UM.ME.[A', Word('{lu₂@v}UM.ME.[A', parts=[
        ValueToken('{'), Reading.of('lu', 2, modifiers=['@v']),
        ValueToken('}'), ValueToken('UM'), Joiner(atf.Joiner.DOT),
        ValueToken('ME'), Joiner(atf.Joiner.DOT), ValueToken('['),
        ValueToken('A')
    ])),
    ('{lu₂@v}]KAB.SAR-M[EŠ', Word('{lu₂@v}]KAB.SAR-M[EŠ', parts=[
        ValueToken('{'), Reading.of('lu', 2, modifiers=['@v']),
        ValueToken('}'), ValueToken(']'), ValueToken('KAB'),
        Joiner(atf.Joiner.DOT), ValueToken('SAR'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('M[EŠ')
    ])),
    ('MIN<(ta-ne₂-hi)>', Word('MIN<(ta-ne₂-hi)>', parts=[
        ValueToken('MIN<(ta-ne₂-hi)>')
    ])),
    ('UN#', Word('UN#', parts=[ValueToken('UN#')])),
    ('he₂-<(pa₃)>', Word('he₂-<(pa₃)>', parts=[
        Reading.of('he', 2), Joiner(atf.Joiner.HYPHEN), ValueToken('<('),
        Reading.of('pa', 3), ValueToken(')>')
    ])),
    ('{[i]ti}AB', Word('{[i]ti}AB', parts=[
        ValueToken('{'), ValueToken('['), Reading.of('i]ti'),
        ValueToken('}'), ValueToken('AB')
    ])),
    ('in]-', Word('in]-', parts=[
        Reading.of('in'), ValueToken(']'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('<en-da-ab>', Word('<en-da-ab>', parts=[
        ValueToken('<'), Reading.of('en'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('da'), Joiner(atf.Joiner.HYPHEN), Reading.of('ab'),
        ValueToken('>')
    ])),
    ('me-e-li-°\\ku°', Word('me-e-li-°\\ku°', parts=[
        Reading.of('me'), Joiner(atf.Joiner.HYPHEN), Reading.of('e'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('li'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), ValueToken('\\'), Reading.of('ku'), ValueToken('°')
    ])),
    ('°me-e-li\\°-ku', Word('°me-e-li\\°-ku', parts=[
        ValueToken('°'), Reading.of('me'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('e'), Joiner(atf.Joiner.HYPHEN), Reading.of('li'),
        ValueToken('\\'), ValueToken('°'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('ku')
    ])),
    ('me-°e\\li°-ku', Word('me-°e\\li°-ku', parts=[
        Reading.of('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        Reading.of('e'), ValueToken('\\'), Reading.of('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
    ])),
    ('me-°e\\li°-me-°e\\li°-ku', Word('me-°e\\li°-me-°e\\li°-ku', parts=[
        Reading.of('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        Reading.of('e'), ValueToken('\\'), Reading.of('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('me'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), Reading.of('e'), ValueToken('\\'), Reading.of('li'),
        ValueToken('°'), Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
    ])),
    ('...{d}kur', Word('...{d}kur', parts=[
        UnknownNumberOfSigns(), ValueToken('{'), Reading.of('d'),
        ValueToken('}'), Reading.of('kur')
    ])),
    ('kur{d}...', Word('kur{d}...', parts=[
        Reading.of('kur'), ValueToken('{'), Reading.of('d'), ValueToken('}'),
        UnknownNumberOfSigns()
    ])),
    ('...-kur-...', Word('...-kur-...', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.HYPHEN), Reading.of('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns()
    ])),
    ('kur-...-kur-...-kur', Word('kur-...-kur-...-kur', parts=[
        Reading.of('kur'), Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), Reading.of('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), Reading.of('kur')
    ])),
    ('...]-ku', Word('...]-ku', parts=[
        UnknownNumberOfSigns(), ValueToken(']'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('ku')
    ])),
    ('ku-[...', Word('ku-[...', parts=[
        Reading.of('ku'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
        UnknownNumberOfSigns()
    ])),
    ('....ku', Word('....ku', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.DOT), Reading.of('ku')
    ])),
    ('ku....', Word('ku....', parts=[
        Reading.of('ku'), Joiner(atf.Joiner.DOT), UnknownNumberOfSigns()
    ])),
    ('(x)]', Word('(x)]', parts=[
        ValueToken('('), UnclearSign(), ValueToken(')'), ValueToken(']')
    ])),
    ('[{d}UTU', Word('[{d}UTU', parts=[
        ValueToken('['), ValueToken('{'), Reading.of('d'), ValueToken('}'),
        ValueToken('UTU')
    ])),
    ('{m#}[{d}AG-sa-lim', Word('{m#}[{d}AG-sa-lim', parts=[
        ValueToken('{'), Reading.of('m', flags=[atf.Flag.DAMAGE]),
        ValueToken('}'), ValueToken('['), ValueToken('{'), Reading.of('d'),
        ValueToken('}'), ValueToken('AG'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('sa'), Joiner(atf.Joiner.HYPHEN), Reading.of('lim')
    ])),
    ('ša#-[<(mu-un-u₅)>]', Word('ša#-[<(mu-un-u₅)>]', parts=[
        Reading.of('ša', flags=[atf.Flag.DAMAGE]), Joiner(atf.Joiner.HYPHEN),
        ValueToken('['), ValueToken('<('), Reading.of('mu'),
        Joiner(atf.Joiner.HYPHEN), Reading.of('un'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('u', 5), ValueToken(')>'), ValueToken(']')
    ])),
    ('|UM×(ME.DA)|-b[i?', Word('|UM×(ME.DA)|-b[i?', parts=[
        ValueToken('|UM×(ME.DA)|'), Joiner(atf.Joiner.HYPHEN),
        Reading.of('b[i', flags=[atf.Flag.UNCERTAIN])
    ])),
    ('mu-un;-e₃', Word('mu-un;-e₃', parts=[
        Reading.of('mu'), Joiner(atf.Joiner.HYPHEN), Reading.of('un'),
        InWordNewline(), Joiner(atf.Joiner.HYPHEN), Reading.of('e', 3)
    ]))
])
def test_word(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
    ('<{10}>', LoneDeterminative('<{10}>', parts=[
        ValueToken('<'), ValueToken('{'),  Number.of(10), ValueToken('}'),
        ValueToken('>')
    ])),
    ('{ud]u?}', LoneDeterminative('{ud]u?}', parts=[
        ValueToken('{'), Reading.of('ud]u', flags=[atf.Flag.UNCERTAIN]),
        ValueToken('}')
    ])),
    ('{u₂#}', LoneDeterminative('{u₂#}', parts=[
        ValueToken('{'), Reading.of('u', 2, flags=[atf.Flag.DAMAGE]),
        ValueToken('}')
    ])),
    ('{lu₂@v}', LoneDeterminative('{lu₂@v}', parts=[
        ValueToken('{'), Reading.of('lu', 2, modifiers=['@v']), ValueToken('}')
    ])),
    ('{k[i]}', LoneDeterminative('{k[i]}', parts=[
        ValueToken('{'), Reading.of('k[i'), ValueToken(']'), ValueToken('}')
    ])),
    ('{[k]i}', LoneDeterminative('{[k]i}', parts=[
        ValueToken('{'), ValueToken('['), Reading.of('k]i'), ValueToken('}')
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
    '0',
    '01'
])
def test_invalid(parser, atf):
    with pytest.raises((UnexpectedInput, ParseError)):
        parser(atf)

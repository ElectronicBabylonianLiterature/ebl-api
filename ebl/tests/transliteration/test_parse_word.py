import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.sign_tokens import UnidentifiedSign, \
    UnclearSign
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
    ('12', Word('12', parts=[ValueToken('12')])),
    ('GAL', Word('GAL', parts=[ValueToken('GAL')])),
    ('|GAL|', Word('|GAL|', parts=[ValueToken('|GAL|')])),
    ('x-ti', Word('x-ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.HYPHEN), ValueToken('ti')
    ])),
    ('x.ti', Word('x.ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.DOT), ValueToken('ti')
    ])),
    ('x+ti', Word('x+ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.PLUS), ValueToken('ti')
    ])),
    ('x:ti', Word('x:ti', parts=[
        UnclearSign(), Joiner(atf.Joiner.COLON), ValueToken('ti')
    ])),
    ('ti-X', Word('ti-X', parts=[
        ValueToken('ti'), Joiner(atf.Joiner.HYPHEN), UnidentifiedSign()
    ])),
    ('r]u-u₂-qu', Word('r]u-u₂-qu', parts=[
        ValueToken('r]u'), Joiner(atf.Joiner.HYPHEN), ValueToken('u₂'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('qu')
    ])),
    ('ru?-u₂-qu', Word('ru?-u₂-qu', parts=[
        ValueToken('ru?'), Joiner(atf.Joiner.HYPHEN), ValueToken('u₂'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('qu')
    ])),
    ('na-a[n-', Word('na-a[n-', parts=[
        ValueToken('na'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('a[n'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('-ku]-nu', Word('-ku]-nu', parts=[
        Joiner(atf.Joiner.HYPHEN), ValueToken('ku'), ValueToken(']'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('nu')
    ])),
    ('gid₂', Word('gid₂', parts=[ValueToken('gid₂')])),
    ('|U₄&KAM₂|', Word('|U₄&KAM₂|', parts=[ValueToken('|U₄&KAM₂|')])),
    ('U₄].14.KAM₂', Word('U₄].14.KAM₂', parts=[
        ValueToken('U₄'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        ValueToken('14'), Joiner(atf.Joiner.DOT), ValueToken('KAM₂')
    ])),
    ('{ku}nu', Word('{ku}nu', parts=[
        ValueToken('{'), ValueToken('ku'), ValueToken('}'), ValueToken('nu')
    ])),
    ('{{ku}}nu', Word('{{ku}}nu', parts=[
        ValueToken('{{'), ValueToken('ku'), ValueToken('}}'), ValueToken('nu')
    ])),
    ('ku{{nu}}', Word('ku{{nu}}', parts=[
        ValueToken('ku'), ValueToken('{{'), ValueToken('nu'), ValueToken('}}')
    ])),
    ('ku{nu}', Word('ku{nu}', parts=[
        ValueToken('ku'), ValueToken('{'), ValueToken('nu'), ValueToken('}')
    ])),
    ('ku{{nu}}si', Word('ku{{nu}}si', parts=[
        ValueToken('ku'), ValueToken('{{'), ValueToken('nu'), ValueToken('}}'),
        ValueToken('si')
    ])),
    ('{iti}]ŠE', Word('{iti}]ŠE', parts=[
        ValueToken('{'), ValueToken('iti'), ValueToken('}'), ValueToken(']'),
        ValueToken('ŠE')
    ])),
    ('šu/|BI×IS|', Word('šu/|BI×IS|', parts=[ValueToken('šu/|BI×IS|')])),
    ('{kur}aš+šur', Word('{kur}aš+šur', parts=[
        ValueToken('{'), ValueToken('kur'), ValueToken('}'), ValueToken('aš'),
        Joiner(atf.Joiner.PLUS), ValueToken('šur')
    ])),
    ('i-le-ʾe-[e', Word('i-le-ʾe-[e', parts=[
        ValueToken('i'), Joiner(atf.Joiner.HYPHEN), ValueToken('le'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('ʾe'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('['), ValueToken('e')
    ])),
    ('U₄.27/29.KAM', Word('U₄.27/29.KAM', parts=[
        ValueToken('U₄'), Joiner(atf.Joiner.DOT), ValueToken('27/29'),
        Joiner(atf.Joiner.DOT), ValueToken('KAM')
    ])),
    ('x/m[a', Word('x/m[a', parts=[ValueToken('x/m[a')])),
    ('SAL.{+mu-ru-ub}', Word('SAL.{+mu-ru-ub}', parts=[
        ValueToken('SAL'), Joiner(atf.Joiner.DOT), ValueToken('{+'),
        ValueToken('mu'), Joiner(atf.Joiner.HYPHEN), ValueToken('ru'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('ub'), ValueToken('}')
    ])),
    ('{+mu-ru-ub}[LA', Word('{+mu-ru-ub}[LA', parts=[
        ValueToken('{+'), ValueToken('mu'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('ru'), Joiner(atf.Joiner.HYPHEN), ValueToken('ub'),
        ValueToken('}'), ValueToken('['), ValueToken('LA')
    ])),
    ('I.{d}', Word('I.{d}', parts=[
        ValueToken('I'), Joiner(atf.Joiner.DOT), ValueToken('{'),
        ValueToken('d'), ValueToken('}')
    ])),
    ('{d}[UTU?', Word('{d}[UTU?', parts=[
        ValueToken('{'), ValueToken('d'), ValueToken('}'), ValueToken('['),
        ValueToken('UTU?')
    ])),
    ('.x.KAM', Word('.x.KAM', parts=[
        Joiner(atf.Joiner.DOT), UnclearSign(), Joiner(atf.Joiner.DOT),
        ValueToken('KAM')
    ])),
    ('3.AM₃', Word('3.AM₃', parts=[
        ValueToken('3'), Joiner(atf.Joiner.DOT), ValueToken('AM₃')
    ])),
    ('<{10}>bu', Word('<{10}>bu', parts=[
        ValueToken('<'), ValueToken('{'), ValueToken('10'), ValueToken('}'),
        ValueToken('>'), ValueToken('bu')
    ])),
    ('KA₂?].DINGIR.RA[{ki?}', Word('KA₂?].DINGIR.RA[{ki?}', parts=[
        ValueToken('KA₂?'), ValueToken(']'), Joiner(atf.Joiner.DOT),
        ValueToken('DINGIR'), Joiner(atf.Joiner.DOT), ValueToken('RA'),
        ValueToken('['), ValueToken('{'), ValueToken('ki?'), ValueToken('}')
    ])),
    ('{d?}nu?-di]m₂?-mu[d?', Word('{d?}nu?-di]m₂?-mu[d?', parts=[
        ValueToken('{'), ValueToken('d?'), ValueToken('}'), ValueToken('nu?'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('di]m₂?'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('mu[d?')
    ])),
    ('<GAR?>', Word('<GAR?>', parts=[
        ValueToken('<'), ValueToken('GAR?'), ValueToken('>')
    ])),
    ('lu₂@v', Word('lu₂@v', parts=[ValueToken('lu₂@v')])),
    ('{lu₂@v}UM.ME.[A', Word('{lu₂@v}UM.ME.[A', parts=[
        ValueToken('{'), ValueToken('lu₂@v'), ValueToken('}'),
        ValueToken('UM'), Joiner(atf.Joiner.DOT), ValueToken('ME'),
        Joiner(atf.Joiner.DOT), ValueToken('['), ValueToken('A')
    ])),
    ('{lu₂@v}]KAB.SAR-M[EŠ', Word('{lu₂@v}]KAB.SAR-M[EŠ', parts=[
        ValueToken('{'), ValueToken('lu₂@v'), ValueToken('}'), ValueToken(']'),
        ValueToken('KAB'), Joiner(atf.Joiner.DOT), ValueToken('SAR'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('M[EŠ')
    ])),
    ('MIN<(ta-ne₂-hi)>', Word('MIN<(ta-ne₂-hi)>', parts=[
        ValueToken('MIN'), ValueToken('<('), ValueToken('ta'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('ne₂'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('hi'), ValueToken(')>')
    ])),
    ('UN#', Word('UN#', parts=[ValueToken('UN#')])),
    ('he₂-<(pa₃)>', Word('he₂-<(pa₃)>', parts=[
        ValueToken('he₂'), Joiner(atf.Joiner.HYPHEN), ValueToken('<('),
        ValueToken('pa₃'), ValueToken(')>')
    ])),
    ('{[i]ti}AB', Word('{[i]ti}AB', parts=[
        ValueToken('{'), ValueToken('['), ValueToken('i]ti'),
        ValueToken('}'), ValueToken('AB')
    ])),
    ('in]-', Word('in]-', parts=[
        ValueToken('in'), ValueToken(']'), Joiner(atf.Joiner.HYPHEN)
    ])),
    ('<en-da-ab>', Word('<en-da-ab>', parts=[
        ValueToken('<'), ValueToken('en'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('da'), Joiner(atf.Joiner.HYPHEN), ValueToken('ab'),
        ValueToken('>')
    ])),
    ('me-e-li-°\\ku°', Word('me-e-li-°\\ku°', parts=[
        ValueToken('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('e'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('li'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), ValueToken('\\'), ValueToken('ku'), ValueToken('°')
    ])),
    ('°me-e-li\\°-ku', Word('°me-e-li\\°-ku', parts=[
        ValueToken('°'), ValueToken('me'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('e'), Joiner(atf.Joiner.HYPHEN), ValueToken('li'),
        ValueToken('\\'), ValueToken('°'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('ku')
    ])),
    ('me-°e\\li°-ku', Word('me-°e\\li°-ku', parts=[
        ValueToken('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        ValueToken('e'), ValueToken('\\'), ValueToken('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('ku')
    ])),
    ('me-°e\\li°-me-°e\\li°-ku', Word('me-°e\\li°-me-°e\\li°-ku', parts=[
        ValueToken('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
        ValueToken('e'), ValueToken('\\'), ValueToken('li'), ValueToken('°'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('me'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('°'), ValueToken('e'), ValueToken('\\'), ValueToken('li'),
        ValueToken('°'), Joiner(atf.Joiner.HYPHEN), ValueToken('ku')
    ])),
    ('...{d}kur', Word('...{d}kur', parts=[
        UnknownNumberOfSigns(), ValueToken('{'), ValueToken('d'),
        ValueToken('}'), ValueToken('kur')
    ])),
    ('kur{d}...', Word('kur{d}...', parts=[
        ValueToken('kur'), ValueToken('{'), ValueToken('d'), ValueToken('}'),
        UnknownNumberOfSigns()
    ])),
    ('...-kur-...', Word('...-kur-...', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.HYPHEN), ValueToken('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns()
    ])),
    ('kur-...-kur-...-kur', Word('kur-...-kur-...-kur', parts=[
        ValueToken('kur'), Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), ValueToken('kur'),
        Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
        Joiner(atf.Joiner.HYPHEN), ValueToken('kur')
    ])),
    ('...]-ku', Word('...]-ku', parts=[
        UnknownNumberOfSigns(), ValueToken(']'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('ku')
    ])),
    ('ku-[...', Word('ku-[...', parts=[
        ValueToken('ku'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
        UnknownNumberOfSigns()
    ])),
    ('....ku', Word('....ku', parts=[
        UnknownNumberOfSigns(), Joiner(atf.Joiner.DOT), ValueToken('ku')
    ])),
    ('ku....', Word('ku....', parts=[
        ValueToken('ku'), Joiner(atf.Joiner.DOT), UnknownNumberOfSigns()
    ])),
    ('(x)]', Word('(x)]', parts=[
        ValueToken('('), UnclearSign(), ValueToken(')'), ValueToken(']')
    ])),
    ('[{d}UTU', Word('[{d}UTU', parts=[
        ValueToken('['), ValueToken('{'), ValueToken('d'), ValueToken('}'),
        ValueToken('UTU')
    ])),
    ('{m#}[{d}AG-sa-lim', Word('{m#}[{d}AG-sa-lim', parts=[
        ValueToken('{'), ValueToken('m#'), ValueToken('}'), ValueToken('['),
        ValueToken('{'), ValueToken('d'), ValueToken('}'), ValueToken('AG'),
        Joiner(atf.Joiner.HYPHEN), ValueToken('sa'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('lim')
    ])),
    ('ša#-[<(mu-un-u₅)>]', Word('ša#-[<(mu-un-u₅)>]', parts=[
        ValueToken('ša#'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
        ValueToken('<('), ValueToken('mu'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('un'), Joiner(atf.Joiner.HYPHEN), ValueToken('u₅'),
        ValueToken(')>'), ValueToken(']')
    ])),
    ('|UM×(ME.DA)|-b[i?', Word('|UM×(ME.DA)|-b[i?', parts=[
        ValueToken('|UM×(ME.DA)|'), Joiner(atf.Joiner.HYPHEN),
        ValueToken('b[i?')
    ])),
    ('mu-un;-e₃', Word('mu-un;-e₃', parts=[
        ValueToken('mu'), Joiner(atf.Joiner.HYPHEN), ValueToken('un'),
        InWordNewline(), Joiner(atf.Joiner.HYPHEN), ValueToken('e₃')
    ]))
])
def test_word(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize('parser', [
    parse_word
])
@pytest.mark.parametrize('atf,expected', [
    ('<{10}>', LoneDeterminative('<{10}>', parts=[
        ValueToken('<'), ValueToken('{'),  ValueToken('10'), ValueToken('}'),
        ValueToken('>')
    ])),
    ('{ud]u?}', LoneDeterminative('{ud]u?}', parts=[
        ValueToken('{'), ValueToken('ud]u?'), ValueToken('}')
    ])),
    ('{u₂#}', LoneDeterminative('{u₂#}', parts=[
        ValueToken('{'), ValueToken('u₂#'), ValueToken('}')
    ])),
    ('{lu₂@v}', LoneDeterminative('{lu₂@v}', parts=[
        ValueToken('{'), ValueToken('lu₂@v'), ValueToken('}')
    ])),
    ('{k[i]}', LoneDeterminative('{k[i]}', parts=[
        ValueToken('{'), ValueToken('k[i'), ValueToken(']'), ValueToken('}')
    ])),
    ('{[k]i}', LoneDeterminative('{[k]i}', parts=[
        ValueToken('{'), ValueToken('['), ValueToken('k]i'), ValueToken('}')
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

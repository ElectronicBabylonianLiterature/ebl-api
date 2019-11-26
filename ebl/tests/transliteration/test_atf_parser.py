import pytest
from hamcrest import assert_that, contains, has_entries, starts_with

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import Side, \
    DocumentOrientedGloss, BrokenAway, PerhapsBrokenAway, Erasure, \
    OmissionOrRemoval
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Divider, UnidentifiedSign, \
    UnclearSign, Reading, Number
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (LanguageShift,
                                               LineContinuation,
                                               UnknownNumberOfSigns,
                                               Tabulation,
                                               CommentaryProtocol, ValueToken,
                                               Column, Variant)
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError
from ebl.transliteration.domain.word_tokens import Partial, ErasureState, \
    Word, LoneDeterminative, Joiner, InWordNewline

DEFAULT_LANGUAGE = Language.AKKADIAN


@pytest.mark.parametrize('parser,version', [
    (parse_atf_lark, f'{atf.ATF_PARSER_VERSION}')
])
def test_parser_version(parser, version):
    assert parser('1. kur').parser_version == version


@pytest.mark.parametrize('parser', [
    parse_atf_lark
])
@pytest.mark.parametrize('line,expected_tokens', [
    ('', []),
    ('\n', []),
    ('#first\n\n#second', [
        ControlLine.of_single('#', ValueToken('first')),
        EmptyLine(),
        ControlLine.of_single('#', ValueToken('second'))
    ]),
    ('#first\n \n#second', [
        ControlLine.of_single('#', ValueToken('first')),
        EmptyLine(),
        ControlLine.of_single('#', ValueToken('second'))
    ]),
    ('&K11111', [
        ControlLine.of_single('&', ValueToken('K11111'))
    ]),
    ('@reverse', [
        ControlLine.of_single('@', ValueToken('reverse'))
    ]),
    ('$ (end of side)', [
        ControlLine.of_single('$', ValueToken(' (end of side)'))
    ]),
    ('#some notes', [
        ControlLine.of_single('#', ValueToken('some notes'))
    ]),
    ('=: continuation', [
        ControlLine.of_single('=:', ValueToken(' continuation'))
    ]),
    ('a+1.a+2. šu', [
        TextLine('a+1.a+2.', (Word('šu', parts=[Reading.of('šu')]),))
    ]),
    ('1. ($___$)', [
        TextLine('1.', (Tabulation('($___$)'),))
    ]),
    ('1. ... [...] (...) [(...)]', [
        TextLine('1.', (
                UnknownNumberOfSigns(),
                BrokenAway('['),
                UnknownNumberOfSigns(),
                BrokenAway(']'),
                PerhapsBrokenAway('('),
                UnknownNumberOfSigns(),
                PerhapsBrokenAway(')'),
                BrokenAway('['),
                PerhapsBrokenAway('('),
                UnknownNumberOfSigns(),
                PerhapsBrokenAway(')'),
                BrokenAway(']')
        ))
    ]),
    ('1. [(x x x)]', [
        TextLine('1.', (
            Word('[(x', parts=[
                ValueToken('['), ValueToken('('), UnclearSign()
            ]),
            Word('x', parts=[UnclearSign()]),
            Word('x)]', parts=[
                UnclearSign(), ValueToken(')'), ValueToken(']')
            ])
        ))
    ]),
    ('1. <en-da-ab-su₈ ... >', [
        TextLine('1.', (
            Word('<en-da-ab-su₈', parts=[
                ValueToken('<'), Reading.of('en'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('da'), Joiner(atf.Joiner.HYPHEN), Reading.of('ab'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('su', 8)
            ]),
            UnknownNumberOfSigns(),
            OmissionOrRemoval('>')
        ))
    ]),
    ('1. & &12', [
        TextLine('1.', (Column(), Column(12)))
    ]),
    ('1. | : :\' :" :. :: ; /', [
        TextLine('1.', (
                Divider('|'),
                Divider(':'),
                Divider(":'"),
                Divider(':"'),
                Divider(':.'),
                Divider('::'),
                Divider(';'),
                Divider('/')
        ))
    ]),
    ("1. |/: :'/sal //: ://", [
        TextLine('1.', (
                Variant.of(Divider('|'), Divider(':')),
                Variant.of(Divider(":'"),
                           Word('sal', parts=[Reading.of('sal')])),
                Variant.of(Divider('/'), Divider(':')),
                Variant.of(Divider(':'), Divider('/'))
        ))
    ]),
    ('1. me-e+li  me.e:li :\n2. ku', [
        TextLine('1.', (
            Word('me-e+li', parts=[
                Reading.of('me'), Joiner(atf.Joiner.HYPHEN), Reading.of('e'),
                Joiner(atf.Joiner.PLUS), Reading.of('li')
            ]),
            Word('me.e:li', parts=[
                Reading.of('me'), Joiner(atf.Joiner.DOT), Reading.of('e'),
                Joiner(atf.Joiner.COLON), Reading.of('li')
            ]),
            Divider(':')
        )),
        TextLine('2.', (
            Word('ku', parts=[Reading.of('ku')]),
        ))
    ]),
    ('1. |GAL|', [
        TextLine('1.', (
            Word('|GAL|', parts=[ValueToken('|GAL|')]),
        ))
    ]),
    ('1. !qt !bs !cm !zz', [
        TextLine('1.', (
            CommentaryProtocol('!qt'),
            CommentaryProtocol('!bs'),
            CommentaryProtocol('!cm'),
            CommentaryProtocol('!zz')
        ))
    ]),
    ('1. x X x?# X#!', [
        TextLine('1.', (
            Word('x', parts=[UnclearSign()]),
            Word('X', parts=[UnidentifiedSign()]),
            Word('x?#', parts=[UnclearSign([atf.Flag.UNCERTAIN,
                                           atf.Flag.DAMAGE])]),
            Word('X#!', parts=[UnidentifiedSign([atf.Flag.DAMAGE,
                                                atf.Flag.CORRECTION])])
        ))
    ]),
    ('1. x-ti ti-X', [
        TextLine('1.', (
            Word('x-ti', parts=[
                UnclearSign(), Joiner(atf.Joiner.HYPHEN), Reading.of('ti')
            ]),
            Word('ti-X', parts=[
                Reading.of('ti'), Joiner(atf.Joiner.HYPHEN), UnidentifiedSign()
            ])
        ))
    ]),
    ('1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku', [
        TextLine('1.', (
            BrokenAway('['),
            UnknownNumberOfSigns(),
            Word('r]u?-u₂-qu', parts=[
                Reading.of('r]u', flags=[atf.Flag.UNCERTAIN]),
                Joiner(atf.Joiner.HYPHEN), Reading.of('u', 2),
                Joiner(atf.Joiner.HYPHEN), Reading.of('qu')
            ]),
            Word('na-a[n-...]', parts=[
                Reading.of('na'), Joiner(atf.Joiner.HYPHEN), Reading.of('a[n'),
                Joiner(atf.Joiner.HYPHEN), UnknownNumberOfSigns(),
                ValueToken(']')
            ]),
        )),
        TextLine('2.', (
            Word('ši-[ku-...-ku]-nu', parts=[
                Reading.of('ši'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
                Reading.of('ku'), Joiner(atf.Joiner.HYPHEN),
                UnknownNumberOfSigns(), Joiner(atf.Joiner.HYPHEN),
                Reading.of('ku'), ValueToken(']'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('nu')
            ]),
        )),
        TextLine('3.', (
            Word('[...]-ku', parts=[
                ValueToken('['), UnknownNumberOfSigns(), ValueToken(']'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
            ]),
        ))
    ]),
    ('1. ša₃] [{d}UTU [ :', [
        TextLine('1.', (
            Word('ša₃]', parts=[Reading.of('ša', 3), ValueToken(']')]),
            Word('[{d}UTU', parts=[
                ValueToken('['), ValueToken('{'), Reading.of('d'),
                ValueToken('}'), ValueToken('UTU')]),
            BrokenAway('['),
            Divider(':')
        ))
    ]),
    ('1. [...]-qa-[...]-ba-[...]\n2. pa-[...]', [
        TextLine('1.', (
            Word('[...]-qa-[...]-ba-[...]', parts=[
                ValueToken('['), UnknownNumberOfSigns(), ValueToken(']'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('qa'),
                Joiner(atf.Joiner.HYPHEN), ValueToken('['),
                UnknownNumberOfSigns(), ValueToken(']'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('ba'),
                Joiner(atf.Joiner.HYPHEN), ValueToken('['),
                UnknownNumberOfSigns(), ValueToken(']')
            ]),
        )),
        TextLine('2.', (
            Word('pa-[...]', parts=[
                Reading.of('pa'), Joiner(atf.Joiner.HYPHEN), ValueToken('['),
                UnknownNumberOfSigns(), ValueToken(']')
            ]),
        ))
    ]),
    ('1. [a?-ku (...)]\n2. [a?-ku (x)]', [
        TextLine('1.', (
            Word('[a?-ku', parts=[
                ValueToken('['), Reading.of('a', flags=[atf.Flag.UNCERTAIN]),
                Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
            ]),
            PerhapsBrokenAway('('),
            UnknownNumberOfSigns(),
            PerhapsBrokenAway(')'),
            BrokenAway(']')
        )),
        TextLine('2.', (
            Word('[a?-ku', parts=[
                ValueToken('['), Reading.of('a', flags=[atf.Flag.UNCERTAIN]),
                Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
            ]),
            Word('(x)]', parts=[
                ValueToken('('), UnclearSign(), ValueToken(')'),
                ValueToken(']')
            ])
        )),
    ]),
    ('1. [...+ku....] [....ku+...]', [
        TextLine('1.', (
            Word('[...+ku....]', parts=[
                ValueToken('['), UnknownNumberOfSigns(),
                Joiner(atf.Joiner.PLUS), Reading.of('ku'),
                Joiner(atf.Joiner.DOT), UnknownNumberOfSigns(), ValueToken(']')
            ]),
            Word('[....ku+...]', parts=[
                ValueToken('['), UnknownNumberOfSigns(),
                Joiner(atf.Joiner.DOT), Reading.of('ku'),
                Joiner(atf.Joiner.PLUS), UnknownNumberOfSigns(),
                ValueToken(']')
            ])
        ))
    ]),
    (
        ('1. [...] {bu} [...]\n'
         '2. [...]{bu} [...]\n'
         '3. [...] {bu}[...]\n'
         '4. [...]{bu}[...]'),
        [
            TextLine('1.', (
                BrokenAway('['),
                UnknownNumberOfSigns(),
                BrokenAway(']'),
                LoneDeterminative.of_value(
                    '{bu}',
                    Partial(False, False),
                    ErasureState.NONE,
                    [ValueToken('{'), Reading.of('bu'), ValueToken('}')]
                ),
                BrokenAway('['),
                UnknownNumberOfSigns(),
                BrokenAway(']')
            )),
            TextLine('2.', (
                Word('[...]{bu}', parts=[
                    ValueToken('['), UnknownNumberOfSigns(), ValueToken(']'),
                    ValueToken('{'), Reading.of('bu'), ValueToken('}')
                ]),
                BrokenAway('['),
                UnknownNumberOfSigns(),
                BrokenAway(']')
            )),
            TextLine('3.', (
                BrokenAway('['),
                UnknownNumberOfSigns(),
                BrokenAway(']'),
                Word('{bu}[...]', parts=[
                    ValueToken('{'), Reading.of('bu'), ValueToken('}'),
                    ValueToken('['), UnknownNumberOfSigns(), ValueToken(']')
                ])
            )),
            TextLine('4.', (
                Word('[...]{bu}[...]', parts=[
                    ValueToken('['), UnknownNumberOfSigns(), ValueToken(']'),
                    ValueToken('{'), Reading.of('bu'), ValueToken('}'),
                    ValueToken('['), UnknownNumberOfSigns(), ValueToken(']')
                ]),
            ))
        ]
    ),
    ('1. {bu}-nu {bu-bu}-nu\n2. {bu-bu}', [
        TextLine('1.', (
            Word('{bu}-nu', parts=[
                ValueToken('{'), Reading.of('bu'), ValueToken('}'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('nu')
            ]),
            Word('{bu-bu}-nu', parts=[
                ValueToken('{'), Reading.of('bu'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('bu'), ValueToken('}'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('nu')
            ])
        )),
        TextLine('2.', (
            LoneDeterminative.of_value(
                '{bu-bu}',
                Partial(False, False),
                ErasureState.NONE,
                [ValueToken('{'), Reading.of('bu'), Joiner(atf.Joiner.HYPHEN),
                 Reading.of('bu'), ValueToken('}')]
            ),
        )),
    ]),
    ('1. KIMIN {u₂#}[...] {u₂#} [...]', [
        TextLine('1.', (
            Word('KIMIN', parts=[ValueToken('KIMIN')]),
            Word('{u₂#}[...]', parts=[
                ValueToken('{'), Reading.of('u', 2, flags=[atf.Flag.DAMAGE]),
                ValueToken('}'), ValueToken('['), UnknownNumberOfSigns(),
                ValueToken(']')
            ]),
            LoneDeterminative.of_value(
                '{u₂#}',
                Partial(False, False),
                ErasureState.NONE,
                [ValueToken('{'), Reading.of('u', 2, flags=[atf.Flag.DAMAGE]),
                 ValueToken('}')]
            ),
            BrokenAway('['),
            UnknownNumberOfSigns(),
            BrokenAway(']')
        ))
    ]),
    ('1. šu gid₂\n2. U₄].14.KAM₂ U₄.15.KAM₂', [
        TextLine('1.', (
            Word('šu', parts=[Reading.of('šu')]),
            Word('gid₂', parts=[Reading.of('gid', 2)])
        )),
        TextLine('2.', (
            Word('U₄].14.KAM₂', parts=[
                ValueToken('U₄'), ValueToken(']'), Joiner(atf.Joiner.DOT),
                Number.of(14), Joiner(atf.Joiner.DOT), ValueToken('KAM₂')
            ]),
            Word('U₄.15.KAM₂', parts=[
                ValueToken('U₄'), Joiner(atf.Joiner.DOT), Number.of(15),
                Joiner(atf.Joiner.DOT), ValueToken('KAM₂')
            ])
        ))
    ]),
    ('1. {(he-pi₂ eš-šu₂)}\n2. {(NU SUR)}', [
        TextLine('1.', (
                DocumentOrientedGloss('{('),
                Word('he-pi₂', parts=[
                    Reading.of('he'), Joiner(atf.Joiner.HYPHEN),
                    Reading.of('pi', 2)
                ]),
                Word('eš-šu₂', parts=[
                    Reading.of('eš'), Joiner(atf.Joiner.HYPHEN),
                    Reading.of('šu', 2)
                ]),
                DocumentOrientedGloss(')}')
        )),
        TextLine('2.', (
                DocumentOrientedGloss('{('),
                Word('NU', parts=[ValueToken('NU')]),
                Word('SUR', parts=[ValueToken('SUR')]),
                DocumentOrientedGloss(')}')
        ))
    ]),
    ('1.  sal/: šim ', [
        TextLine('1.', (
            Variant.of(Word('sal', parts=[Reading.of('sal')]),
                       Divider(':')),
            Word('šim', parts=[Reading.of('šim')])))
    ]),
    ('1. °me-e-li\\ku°', [
        TextLine('1.', (
            Erasure('°', Side.LEFT),
            Word('me-e-li', erasure=ErasureState.ERASED, parts=[
                Reading.of('me'), Joiner(atf.Joiner.HYPHEN), Reading.of('e'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('li')
            ]),
            Erasure('\\', Side.CENTER),
            Word('ku', erasure=ErasureState.OVER_ERASED, parts=[
                Reading.of('ku')
            ]),
            Erasure('°', Side.RIGHT),
        )),
    ]),
    ('1. me-e-li-°\\ku°', [
        TextLine('1.', (
            Word('me-e-li-°\\ku°', parts=[
                Reading.of('me'), Joiner(atf.Joiner.HYPHEN), Reading.of('e'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('li'),
                Joiner(atf.Joiner.HYPHEN), ValueToken('°'), ValueToken('\\'),
                Reading.of('ku'), ValueToken('°')
            ]),
        )),
    ]),
    ('1. °me-e-li\\°-ku', [
        TextLine('1.', (
            Word('°me-e-li\\°-ku', parts=[
                ValueToken('°'), Reading.of('me'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('e'), Joiner(atf.Joiner.HYPHEN), Reading.of('li'),
                ValueToken('\\'), ValueToken('°'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('ku')
            ]),
        )),
    ]),
    ('1. me-°e\\li°-ku', [
        TextLine('1.', (
            Word('me-°e\\li°-ku', parts=[
                Reading.of('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
                Reading.of('e'), ValueToken('\\'), Reading.of('li'),
                ValueToken('°'), Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
            ]),
        )),
    ]),
    ('1. me-°e\\li°-me-°e\\li°-ku', [
        TextLine('1.', (
            Word('me-°e\\li°-me-°e\\li°-ku', parts=[
                Reading.of('me'), Joiner(atf.Joiner.HYPHEN), ValueToken('°'),
                Reading.of('e'), ValueToken('\\'), Reading.of('li'),
                ValueToken('°'), Joiner(atf.Joiner.HYPHEN), Reading.of('me'),
                Joiner(atf.Joiner.HYPHEN), ValueToken('°'), Reading.of('e'),
                ValueToken('\\'), Reading.of('li'), ValueToken('°'),
                Joiner(atf.Joiner.HYPHEN), Reading.of('ku')
            ]),
        )),
    ]),
    ('1. sal →', [
        TextLine('1.', (Word('sal', parts=[Reading.of('sal')]),
                        LineContinuation('→')))
    ]),
    ('2. sal →  ', [
        TextLine('2.', (Word('sal', parts=[Reading.of('sal')]),
                        LineContinuation('→')))
    ]),
    ('1. [{(he-pi₂ e]š-šu₂)}', [
        TextLine('1.', (
            BrokenAway('['),
            DocumentOrientedGloss('{('),
            Word('he-pi₂', parts=[
                Reading.of('he'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('pi', 2)
            ]),
            Word('e]š-šu₂', parts=[
                Reading.of('e]š'), Joiner(atf.Joiner.HYPHEN),
                Reading.of('šu', 2)
            ]),
            DocumentOrientedGloss(')}')
        ))
    ]),
    ('1. [{iti}...]', [
        TextLine('1.', (
            Word('[{iti}...]', parts=[
                ValueToken('['), ValueToken('{'), Reading.of('iti'),
                ValueToken('}'), UnknownNumberOfSigns(), ValueToken(']')
            ]),
        ))
    ]),
    ('2. RA{k[i]}', [
        TextLine('2.', (Word('RA{k[i]}', parts=[
            ValueToken('RA'), ValueToken('{'), Reading.of('k[i'),
            ValueToken(']'), ValueToken('}')
        ]),))
    ]),
    ('2. in]-<(...)>', [
        TextLine('2.', (Word('in]-<(...)>', parts=[
            Reading.of('in'), ValueToken(']'), Joiner(atf.Joiner.HYPHEN),
            ValueToken('<('), UnknownNumberOfSigns(), ValueToken(')>')
        ]), ))

    ]),
    ('2. ...{d}kur ... {d}kur', [
        TextLine('2.', (
            Word('...{d}kur', parts=[
                UnknownNumberOfSigns(), ValueToken('{'), Reading.of('d'),
                ValueToken('}'), Reading.of('kur')
            ]),
            UnknownNumberOfSigns(),
            Word('{d}kur', parts=[
                ValueToken('{'), Reading.of('d'), ValueToken('}'),
                Reading.of('kur')
            ])
        ))
    ]),
    ('2. kur{d}... kur{d} ...', [
        TextLine('2.', (
            Word('kur{d}...', parts=[
                Reading.of('kur'), ValueToken('{'), Reading.of('d'),
                ValueToken('}'), UnknownNumberOfSigns()
            ]),
            Word('kur{d}', parts=[
                Reading.of('kur'), ValueToken('{'), Reading.of('d'),
                ValueToken('}'),
            ]),
            UnknownNumberOfSigns()
        ))
    ]),
    ('1. mu-un;-e₃ ;', [
        TextLine('1.', (
            Word('mu-un;-e₃', parts=[
                Reading.of('mu'), Joiner(atf.Joiner.HYPHEN), Reading.of('un'),
                InWordNewline(), Joiner(atf.Joiner.HYPHEN), Reading.of('e', 3)
            ]),
            Divider(';')
        ))
    ])
])
def test_parse_atf(parser, line, expected_tokens):
    assert parser(line).lines == \
           Text.of_iterable(expected_tokens).lines


def test_parse_dividers():
    line, expected_tokens = (r'1. :? :#! :# ::? :.@v /@19* :"@20@c |@v@19!', [
        TextLine('1.', (
                Divider(':', tuple(), (atf.Flag.UNCERTAIN,)),
                Divider(':', tuple(), (atf.Flag.DAMAGE, atf.Flag.CORRECTION)),
                Divider(':', tuple(), (atf.Flag.DAMAGE, )),
                Divider('::', tuple(), (atf.Flag.UNCERTAIN, )),
                Divider(':.', ('@v', ), tuple()),
                Divider('/', ('@19', ), (atf.Flag.COLLATION,)),
                Divider(':"', ('@20', '@c'), tuple()),
                Divider('|', ('@v', '@19'), (atf.Flag.CORRECTION,)),
        ))
    ])
    assert parse_atf_lark(line).lines == \
        Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize('parser', [
    parse_atf_lark
])
def test_parse_atf_invalid(parser):
    with pytest.raises(Exception):
        parser('invalid')


@pytest.mark.parametrize('parser', [
    parse_atf_lark
])
@pytest.mark.parametrize('code,expected_language', [
    ('%ma', Language.AKKADIAN),
    ('%mb', Language.AKKADIAN),
    ('%na', Language.AKKADIAN),
    ('%nb', Language.AKKADIAN),
    ('%lb', Language.AKKADIAN),
    ('%sb', Language.AKKADIAN),
    ('%a', Language.AKKADIAN),
    ('%akk', Language.AKKADIAN),
    ('%eakk', Language.AKKADIAN),
    ('%oakk', Language.AKKADIAN),
    ('%ur3akk', Language.AKKADIAN),
    ('%oa', Language.AKKADIAN),
    ('%ob', Language.AKKADIAN),
    ('%sux', Language.SUMERIAN),
    ('%es', Language.EMESAL),
    ('%foo', DEFAULT_LANGUAGE)
])
def test_parse_atf_language_shifts(parser, code, expected_language):
    word = 'ha-am'
    parts = [Reading.of('ha'), Joiner(atf.Joiner.HYPHEN), Reading.of('am')]
    line = f'1. {word} {code} {word} %sb {word}'

    expected = Text((
        TextLine('1.', (
            Word(word, DEFAULT_LANGUAGE, parts=parts),
            LanguageShift(code), Word(word, expected_language, parts=parts),
            LanguageShift('%sb'), Word(word, Language.AKKADIAN, parts=parts)
        )),
    ))

    assert parser(line).lines == expected.lines


@pytest.mark.parametrize('parser', [
    parse_atf_lark
])
@pytest.mark.parametrize('atf,line_numbers', [
    ('1. x\nthis is not valid', [2]),
    ('1\'. ($____$) x [...]\n$ (too many underscores)', [1]),
    ('1. me°-e\\li°-ku', [1]),
    ('1. me-°e\\li-°ku', [1]),
    ('1\'. → x\n$ (line continuation in the middle)', [1]),
    ('this is not valid\nthis is not valid', [1, 2])
])
def test_invalid_atf(parser, atf, line_numbers):
    with pytest.raises(TransliterationError) as exc_info:
        parser(atf)

    assert_that(exc_info.value.errors, contains(*[has_entries({
        'description': starts_with('Invalid line'),
        'lineNumber': line_number
    }) for line_number in line_numbers]))

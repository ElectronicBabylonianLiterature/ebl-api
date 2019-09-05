import pytest
from hamcrest import assert_that, contains, has_entries, starts_with

from ebl.text.atf import ATF_PARSER_VERSION
from ebl.text.atf_parser import parse_atf
from ebl.text.language import Language
from ebl.text.lark_parser import parse_atf_lark
from ebl.text.line import ControlLine, EmptyLine, TextLine
from ebl.text.text import Text
from ebl.text.token import (BrokenAway, DocumentOrientedGloss, Erasure,
                            ErasureState, LanguageShift, LineContinuation,
                            LoneDeterminative, OmissionOrRemoval, Partial,
                            PerhapsBrokenAway, Side, Token, Word)
from ebl.text.transliteration_error import TransliterationError

DEFAULT_LANGUAGE = Language.AKKADIAN


@pytest.mark.parametrize('parser,version', [
    (parse_atf, ATF_PARSER_VERSION),
    (parse_atf_lark, f'{ATF_PARSER_VERSION}-lark')
])
def test_parser_version(parser, version):
    assert parser('1. kur').parser_version == version


@pytest.mark.parametrize('parser', [
    parse_atf,
    parse_atf_lark
])
@pytest.mark.parametrize('line,expected_tokens', [
    ('', []),
    ('\n', []),
    ('#first\n\n#second', [
        ControlLine.of_single('#', Token('first')),
        EmptyLine(),
        ControlLine.of_single('#', Token('second'))
    ]),
    ('#first\n \n#second', [
        ControlLine.of_single('#', Token('first')),
        EmptyLine(),
        ControlLine.of_single('#', Token('second'))
    ]),
    ('&K11111', [
        ControlLine.of_single('&', Token('K11111'))
    ]),
    ('@reverse', [
        ControlLine.of_single('@', Token('reverse'))
    ]),
    ('$ (end of side)', [
        ControlLine.of_single('$', Token(' (end of side)'))
    ]),
    ('#some notes', [
        ControlLine.of_single('#', Token('some notes'))
    ]),
    ('=: continuation', [
        ControlLine.of_single('=:', Token(' continuation'))
    ]),
    ('a+1.a+2. šu', [
        TextLine('a+1.a+2.', (Word('šu'),))
    ]),
    ('1. ($___$)', [
        TextLine('1.', (Token('($___$)'),))
    ]),
    ('1. ... [...] (...) [(...)]', [
        TextLine('1.', (
                Token('...'),
                BrokenAway('['), Token('...'), BrokenAway(']'),
                PerhapsBrokenAway('('), Token('...'), PerhapsBrokenAway(')'),
                BrokenAway('['), PerhapsBrokenAway('('), Token('...'),
                PerhapsBrokenAway(')'), BrokenAway(']')
        ))
    ]),
    ('1. [(x x x)]', [
        TextLine('1.', (
                BrokenAway('['), PerhapsBrokenAway('('),
                Word('x'),
                Word('x'),
                Word('x'),
                PerhapsBrokenAway(')'), BrokenAway(']')
        ))
    ]),
    ('1. <en-da-ab-su₈ ... >', [
        TextLine('1.', (
                Word('<en-da-ab-su₈'),
                Token('...'),
                OmissionOrRemoval('>')
        ))
    ]),
    ('1. & &12', [
        TextLine('1.', (Token('&'), Token('&12')))
    ]),
    ('1. | : :\' :" :. :: ; /', [
        TextLine('1.', (
                Token('|'),
                Token(':'),
                Token(':\''),
                Token(':"'),
                Token(':.'),
                Token('::'),
                Token(';'),
                Token('/')
        ))
    ]),
    ('1. :? :# ::?', [
        TextLine('1.', (
                Token(':?'),
                Token(':#'),
                Token('::?')
        ))
    ]),
    ('1. me-e-li :\n2. ku', [
        TextLine('1.', (
                Word('me-e-li'),
                Token(':')
        )),
        TextLine('2.', (
                Word('ku'),
        ))
    ]),
    ('1. |GAL|', [
        TextLine('1.', (
                Word('|GAL|'),
        ))
    ]),
    ('1. !qt !bs !cm !zz', [
        TextLine('1.', (
                Token('!qt'), Token('!bs'), Token('!cm'), Token('!zz')
        ))
    ]),
    ('1. x X x# X#', [
        TextLine('1.', (Word('x'), Word('X'), Word('x#'), Word('X#')))
    ]),
    ('1. x-ti ti-X', [
        TextLine('1.', (Word('x-ti'), Word('ti-X')))
    ]),
    ('1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku', [
        TextLine('1.', (
                BrokenAway('['),
                Token('...'),
                Word('r]u?-u₂-qu'),
                Word('na-a[n-'),
                Token('...'),
                BrokenAway(']')
        )),
        TextLine('2.', (
                Word('ši-[ku-'),
                Token('...'),
                Word('-ku]-nu')
        )),
        TextLine('3.', (
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                Word('-ku'),
        ))
    ]),
    ('1. ša₃] [{d}UTU [:', [
        TextLine('1.', (
                Word('ša₃'),
                BrokenAway(']'),
                BrokenAway('['),
                Word('{d}UTU'),
                Token('[:')
        ))
    ]),
    ('1. [...]-qa-[...]-ba-[...]\n2. pa-[...]', [
        TextLine('1.', (
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                Word('-qa-'),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                Word('-ba-'),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
        )),
        TextLine('2.', (
                Word('pa-'),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
        ))
    ]),
    ('1. [a?-ku (...)]\n2. [a?-ku (x)]', [
        TextLine('1.', (
            BrokenAway('['),
            Word('a?-ku'),
            PerhapsBrokenAway('('),
            Token('...'),
            PerhapsBrokenAway(')'),
            BrokenAway(']')
        )),
        TextLine('2.', (
            BrokenAway('['),
            Word('a?-ku'),
            PerhapsBrokenAway('('),
            Word('x'),
            PerhapsBrokenAway(')'),
            BrokenAway(']')
        )),
    ]),
    ('1. [...+ku....] [....ku+...]', [
        TextLine('1.', (
            BrokenAway('['),
            Token('...'),
            Word('+ku.'),
            Token('...'),
            BrokenAway(']'),
            BrokenAway('['),
            Token('...'),
            Word('.ku+'),
            Token('...'),
            BrokenAway(']')
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
                Token('...'),
                BrokenAway(']'),
                LoneDeterminative.of_value('{bu}',
                                           Partial(False, False)),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
            )),
            TextLine('2.', (
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                LoneDeterminative.of_value('{bu}',
                                           Partial(True, False)),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
            )),
            TextLine('3.', (
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                LoneDeterminative.of_value('{bu}',
                                           Partial(False, True)),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
            )),
            TextLine('4.', (
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
                LoneDeterminative.of_value('{bu}',
                                           Partial(True, True)),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']')
            ))
        ]
    ),
    ('1. {bu}-nu {bu-bu}-nu\n2. {bu-bu}', [
        TextLine('1.', (
                Word('{bu}-nu'),
                Word('{bu-bu}-nu')
        )),
        TextLine('2.', (
                LoneDeterminative.of_value('{bu-bu}', Partial(False, False)),
        )),
    ]),
    ('1. KIMIN {u₂#}[...]', [
        TextLine('1.', (
                Word('KIMIN'),
                LoneDeterminative.of_value('{u₂#}', Partial(False, True)),
                BrokenAway('['),
                Token('...'),
                BrokenAway(']'),
        ))
    ]),
    ('1. šu gid₂\n2. U]₄.14.KAM₂ U₄.15.KAM₂', [
        TextLine('1.', (Word('šu'), Word('gid₂'))),
        TextLine('2.', (Word('U]₄.14.KAM₂'), Word('U₄.15.KAM₂')))
    ]),
    ('1. {(he-pi₂ eš-šu₂)}\n2. {(NU SUR)}', [
        TextLine('1.', (
                DocumentOrientedGloss('{('),
                Word('he-pi₂'),
                Word('eš-šu₂'),
                DocumentOrientedGloss(')}')
        )),
        TextLine('2.', (
                DocumentOrientedGloss('{('),
                Word('NU'),
                Word('SUR'),
                DocumentOrientedGloss(')}')
        ))
    ]),
    ('1.  sal/: šim ', [
        TextLine('1.', (Word('sal/:'), Word('šim')))
    ]),
    ('1. °me-e-li\\ku°', [
        TextLine('1.', (
                Erasure('°', Side.LEFT),
                Word('me-e-li', erasure=ErasureState.ERASED),
                Erasure('\\', Side.CENTER),
                Word('ku', erasure=ErasureState.OVER_ERASED),
                Erasure('°', Side.RIGHT),
        )),
    ]),
    ('1. me-e-li-°\\ku°', [
        TextLine('1.', (
                Word('me-e-li-°\\ku°'),
        )),
    ]),
    ('1. °me-e-li\\°-ku', [
        TextLine('1.', (
                Word('°me-e-li\\°-ku'),
        )),
    ]),
    ('1. me-°e\\li°-ku', [
        TextLine('1.', (
                Word('me-°e\\li°-ku'),
        )),
    ]),
    ('1. me-°e\\li°-me-°e\\li°-ku', [
        TextLine('1.', (
                Word('me-°e\\li°-me-°e\\li°-ku'),
        )),
    ]),
    ('1. sal →', [
        TextLine('1.', (Word('sal'), LineContinuation('→')))
    ]),
    ('2. sal →  ', [
        TextLine('2.', (Word('sal'), LineContinuation('→')))
    ]),
    ('1. [{(he-pi₂ e]š-šu₂)}', [
        TextLine('1.', (
            BrokenAway('['), DocumentOrientedGloss('{('), Word('he-pi₂'),
            Word('e]š-šu₂'), DocumentOrientedGloss(')}'))),
    ]),
    ('1. [{iti}...]', [
        TextLine('1.', (
            BrokenAway('['),
            LoneDeterminative('{iti}', partial=Partial(False, True)),
            Token('...'),
            BrokenAway(']')))
    ]),
    ('2. RA{k[i]}', [
        TextLine('2.', (Word('RA{k[i]}'),))
    ]),
    ('2. in]-<(...)>', [
        TextLine('2.', (Word('in]-'),
                        OmissionOrRemoval('<('),
                        Token('...'),
                        OmissionOrRemoval(')>')))

    ]),
])
def test_parse_atf(parser, line, expected_tokens):
    assert parser(line).lines == \
           Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize('parser', [
    parse_atf,
    parse_atf_lark
])
def test_parse_atf_invalid(parser):
    with pytest.raises(Exception):
        parser('invalid')


@pytest.mark.parametrize('parser', [
    parse_atf,
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
    line = f'1. {word} {code} {word} %sb {word}'

    expected = Text((
        TextLine('1.', (
            Word(word, DEFAULT_LANGUAGE),
            LanguageShift(code), Word(word, expected_language),
            LanguageShift('%sb'), Word(word, Language.AKKADIAN)
        )),
    ))

    assert parser(line).lines == expected.lines


@pytest.mark.parametrize('parser', [
    parse_atf,
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
    with pytest.raises(TransliterationError) as excinfo:
        parser(atf)

    assert_that(excinfo.value.errors, contains(*[has_entries({
        'description': starts_with('Invalid line'),
        'lineNumber': line_number
    }) for line_number in line_numbers]))

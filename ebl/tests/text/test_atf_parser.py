import pytest

from ebl.text.atf import AtfSyntaxError
from ebl.text.atf_parser import parse_atf
from ebl.text.language import Language
from ebl.text.line import ControlLine, EmptyLine, TextLine
from ebl.text.text import Text
from ebl.text.token import (DocumentOrientedGloss, LanguageShift,
                            LineContinuation, LoneDeterminative, Partial,
                            Token, Word)


DEFAULT_LANGUAGE = Language.AKKADIAN


@pytest.mark.parametrize('line,expected_tokens', [
    ('', []),
    ('\n', [EmptyLine()]),
    ('#first\n\n#second', [
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
        TextLine('a+1.a+2.', (Word('šu'), ))
    ]),
    ('1. ($___$)', [
        TextLine('1.', (Token('($___$)'), ))
    ]),
    ('1. ... [...] (...) [(...)]', [
        TextLine('1.', (
            Token('...'),
            Token('[...]'),
            Token('(...)'),
            Token('[(...)]')
        ))
    ]),
    ('1. [(x x x)]', [
        TextLine('1.', (
            Word('[(x'),
            Word('x'),
            Word('x)]')
        ))
    ]),
    ('1. <en-da-ab-su₈ ... >', [
        TextLine('1.', (
            Word('<en-da-ab-su₈'),
            Token('...'),
            Token('>')
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
            Token('[...'),
            Word('r]u?-u₂-qu'),
            Word('na-a[n-'),
            Token('...]')
        )),
        TextLine('2.', (
            Word('ši-[ku-'),
            Token('...'),
            Word('-ku]-nu')
        )),
        TextLine('3.', (
            Token('[...]'),
            Word('-ku')
        ))
    ]),
    ('1. ša₃] [{d}UTU [:', [
        TextLine('1.', (
            Word('ša₃]'),
            Word('[{d}UTU'),
            Token('[:')
        ))
    ]),
    ('1. [...]-qa-[...]-ba-[...]\n2. pa-[...]', [
        TextLine('1.', (
            Token('[...]'),
            Word('-qa-'),
            Token('[...]'),
            Word('-ba-'),
            Token('[...]')
        )),
        TextLine('2.', (
            Word('pa-'),
            Token('[...]')
        ))
    ]),
    ('1. [a?-ku (...)]\n2. [a?-ku (x)]', [
        TextLine('1.', (
            Word('[a?-ku'),
            Token('(...)]')
        )),
        TextLine('2.', (
            Word('[a?-ku'),
            Word('(x)]')
        )),
    ]),
    ('1. [...+ku....] [....ku+...]', [
        TextLine('1.', (
            Token('[...'),
            Word('+ku.'),
            Token('...]'),
            Token('[...'),
            Word('.ku+'),
            Token('...]')
        ))
    ]),
    (
        ('1. [...] {bu} [...]\n'
         '2. [...]{bu} [...]\n'
         '3. [...] {bu}[...]\n'
         '4. [...]{bu}[...]'),
        [
            TextLine('1.', (
                Token('[...]'),
                LoneDeterminative.of_value('{bu}', Partial(False, False)),
                Token('[...]')
            )),
            TextLine('2.', (
                Token('[...]'),
                LoneDeterminative.of_value('{bu}', Partial(True, False)),
                Token('[...]')
            )),
            TextLine('3.', (
                Token('[...]'),
                LoneDeterminative.of_value('{bu}', Partial(False, True)),
                Token('[...]')
            )),
            TextLine('4.', (
                Token('[...]'),
                LoneDeterminative.of_value('{bu}', Partial(True, True)),
                Token('[...]')
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
            Token('[...]')
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
    ('1.  sal →', [
        TextLine('1.', (Word('sal'), LineContinuation('→')))
    ]),
    ('2.  sal →  ', [
        TextLine('2.', (Word('sal'), LineContinuation('→')))
    ])
])
def test_parse_atf(line, expected_tokens):
    assert parse_atf(line).lines ==\
        Text.of_iterable(expected_tokens).lines


def test_parse_atf_invalid():
    with pytest.raises(Exception):
        parse_atf('invalid')


@pytest.mark.parametrize("code,expected_language", [
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
def test_parse_atf_language_shifts(code, expected_language):
    word = 'ha-am'
    line = f'1. {word} {code} {word} %sb {word}'

    expected = Text((
        TextLine('1.', (
            Word(word, DEFAULT_LANGUAGE),
            LanguageShift(code), Word(word, expected_language),
            LanguageShift('%sb'), Word(word, Language.AKKADIAN)
        )),
    ))

    assert parse_atf(line) == expected


@pytest.mark.parametrize('atf,line_number', [
    ('1. x\nthis is not valid', 2),
    ('1\'. ($____$) x [...]\n$ (too many underscores)', 1),
    ('1\'. → x\n$ (line continuation in the middle)', 1)
])
def test_invalid_atf(atf, line_number):
    with pytest.raises(AtfSyntaxError,
                       match=f'Line {line_number} is invalid.') as excinfo:
        parse_atf(atf)

    assert excinfo.value.line_number == line_number

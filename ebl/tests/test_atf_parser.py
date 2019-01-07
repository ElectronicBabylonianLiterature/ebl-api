import pytest
from ebl.text.atf import AtfSyntaxError
from ebl.text.atf_parser import parse_atf
from ebl.text.language import Language
from ebl.text.line import EmptyLine, TextLine, ControlLine
from ebl.text.text import Text
from ebl.text.token import Token, Word, LanguageShift


DEFAULT_LANGUAGE = Language.AKKADIAN


@pytest.mark.parametrize("line,expected_tokenization", [
    ('', tuple()),
    ('\n', (EmptyLine(), )),
    ('#first\n\n#second', (
        ControlLine.of_single('#', Token('first')),
        EmptyLine(),
        ControlLine.of_single('#', Token('second'))
    )),
    ('&K11111', (
        ControlLine.of_single('&', Token('K11111')),
    )),
    ('@reverse', (
        ControlLine.of_single('@', Token('reverse')),
    )),
    ('$ (end of side)', (
        ControlLine.of_single('$', Token(' (end of side)')),
    )),
    ('#some notes', (
        ControlLine.of_single('#', Token('some notes')),
    )),
    ('=: continuation', (
        ControlLine.of_single('=:', Token(' continuation')),
    )),
    ('a+1.a+2. šu', (
        TextLine('a+1.a+2.', (Word('šu'), )),
    )),
    ('1. ($___$)', (
        TextLine('1.', (Token('($___$)'), )),
    )),
    ('1. ... [...]', (
        TextLine('1.', (
            Token('...'),
            Token('[...]')
        )),
    )),
    ('1. [(x x x)]', (
        TextLine('1.', (
            Word('[(x'),
            Word('x'),
            Word('x)]')
        )),
    )),
    ('1. & &12', (
        TextLine('1.', (Token('&'), Token('&12'))),
    )),
    ('1. | : ; /', (
        TextLine('1.', (
            Token('|'), Token(':'), Token(';'), Token('/')
        )),
    )),
    ('1. !qt !bs !cm !zz', (
        TextLine('1.', (
            Token('!qt'), Token('!bs'), Token('!cm'), Token('!zz')
        )),
    )),
    ('1. x X x# X#', (
        TextLine('1.', (Word('x'), Word('X'), Word('x#'), Word('X#'))),
    )),
    ('1. x-ti ti-X', (
        TextLine('1.', (Word('x-ti'), Word('ti-X'))),
    )),
    ('1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu', (
        TextLine('1.', (
            Token('[...'), Word('r]u?-u₂-qu'), Word('na-a[n-...]')
        )),
        TextLine('2.', (
            Word('ši-[ku-...-ku]-nu'),
        ))
    )),
    ('1. šu gid₂\n2. U]₄.14.KAM₂ U₄.15.KAM₂', (
        TextLine('1.', (Word('šu'), Word('gid₂'))),
        TextLine('2.', (Word('U]₄.14.KAM₂'), Word('U₄.15.KAM₂')))
    ))
])
def test_parse_atf(line, expected_tokenization):
    assert parse_atf(line) == Text(expected_tokenization)


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


def test_invalid_atf():
    with pytest.raises(AtfSyntaxError,
                       message="Line 1 is invalid.") as excinfo:
        parse_atf('1. x\nthis is not valid')

    assert excinfo.value.line_number == 2

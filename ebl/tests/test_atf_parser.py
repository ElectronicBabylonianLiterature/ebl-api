import pytest
from ebl.fragmentarium.atf_parser import parse_atf

from ebl.fragmentarium.text import (
    Token, Word, Shift, TextLine, ControlLine, EmptyLine
)


@pytest.mark.parametrize("line,expected_tokenization", [
    ('', []),
    ('\n', [EmptyLine()]),
    ('&K11111', [ControlLine.of_single('&', Token('K11111'))]),
    ('@reverse', [ControlLine.of_single('@', Token('reverse'))]),
    ('$ (end of side)', [ControlLine.of_single('$', Token(' (end of side)'))]),
    ('#some notes', [ControlLine.of_single('#', Token('some notes'))]),
    ('=: continuation', [ControlLine.of_single('=:', Token(' continuation'))]),
    ('a+1.a+2. šu', [TextLine('a+1.a+2.', (Word('šu'), ))]),
    ('1. ($___$)', [TextLine('1.', (Token('($___$)'), ))]),
    ('1. ... [...]', [TextLine('1.', (Token('...'), Token('[...]')))]),
    ('1. & &12', [TextLine('1.', (Token('&'), Token('&12')))]),
    ('1. | : ; /', [TextLine('1.', (
        Token('|'), Token(':'), Token(';'), Token('/')
    ))]),
    ('1. !qt !bs !cm !zz', [TextLine('1.', (
        Token('!qt'), Token('!bs'), Token('!cm'), Token('!zz')
    ))]),
    ('1. %es %sux %sb %foo', [TextLine('1.', (
        Shift('%es'), Shift('%sux'), Shift('%sb'), Shift('%foo')
    ))]),
    ('1. x X', [TextLine('1.', (Word('x'), Word('X')))]),
    ('1. x-ti ti-X', [TextLine('1.', (
        Word('x-ti'), Word('ti-X')
    ))]),
    ('1. [... r]u?-u₂-qu na-a[n-...]', [TextLine('1.', (
        Token('[...'), Word('r]u?-u₂-qu'), Word('na-a[n-...]')
    ))]),
    ('1. šu gid₂\n2. U]₄.14.KAM₂ U₄.15.KAM₂', [
        TextLine('1.', (Word('šu'), Word('gid₂'))),
        TextLine('2.', (Word('U]₄.14.KAM₂'), Word('U₄.15.KAM₂')))
    ])
])
def test_parse_atf(line, expected_tokenization):
    assert parse_atf(line) == expected_tokenization


def test_parse_atf_invalid():
    with pytest.raises(Exception):
        parse_atf('invalid')

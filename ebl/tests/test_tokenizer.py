import pytest
from ebl.fragmentarium.tokenizer import tokenize, Line, ControlLine, EmptyLine
from ebl.fragmentarium.tokens import Token, Word, Shift


@pytest.mark.parametrize("line,expected_tokenization", [
    ('', []),
    ('\n', [EmptyLine()]),
    ('&K11111', [ControlLine('&', 'K11111')]),
    ('@reverse', [ControlLine('@', 'reverse')]),
    ('$ (end of side)', [ControlLine('$', ' (end of side)')]),
    ('#some notes', [ControlLine('#', 'some notes')]),
    ('=: continuation', [ControlLine('=:', ' continuation')]),
    ('a+1.a+2. šu', [Line('a+1.a+2.', (Word('šu'), ))]),
    ('1. ($___$)', [Line('1.', (Token('($___$)'), ))]),
    ('1. x X', [Line('1.', (Token('x'), Token('X')))]),
    ('1. ...', [Line('1.', (Token('...'), ))]),
    ('1. & &12', [Line('1.', (Token('&'), Token('&12')))]),
    ('1. | : ; /', [Line('1.', (
        Token('|'), Token(':'), Token(';'), Token('/')
    ))]),
    ('1. !qt !bs !cm !zz', [Line('1.', (
        Token('!qt'), Token('!bs'), Token('!cm'), Token('!zz')
    ))]),
    ('1. %es %sux %sb %foo', [Line('1.', (
        Shift('%es'), Shift('%sux'), Shift('%sb'), Shift('%foo')
    ))]),
    # ('1. x-ti [...]-x-ti ti-X', [Line('1.', [
    #     Token('x-ti'), Token('[...]-x-ti'), Token('ti-X')
    # ])]),
    # ('1. [... r]u?-u₂-qu', [Line('1.', [
    #   Token('[...'), Word('r]u?-u₂-qu')
    # ])]),
    ('1. šu gid₂\n2. U]₄.14.KAM₂ U₄.15.KAM₂', [
        Line('1.', (Word('šu'), Word('gid₂'))),
        Line('2.', (Word('U]₄.14.KAM₂'), Word('U₄.15.KAM₂')))
    ])
])
def test_tokenize(line, expected_tokenization):
    assert tokenize(line) == expected_tokenization


def test_tokenize_invalid():
    with pytest.raises(Exception):
        tokenize('invalid')

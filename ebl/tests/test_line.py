import pytest
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE
from ebl.fragmentarium.line import Line, TextLine, ControlLine, EmptyLine
from ebl.fragmentarium.token import (
    Token, Word, LanguageShift, DEFAULT_NORMALIZED
)


def test_line():
    prefix = '1.'
    token = Token('value')
    line = Line(prefix, (token, ))

    assert line.prefix == prefix
    assert line.content == (token, )


@pytest.mark.parametrize("code,language,normalized", [
    ('%ma', Language.AKKADIAN, False),
    ('%mb', Language.AKKADIAN, False),
    ('%na', Language.AKKADIAN, False),
    ('%nb', Language.AKKADIAN, False),
    ('%lb', Language.AKKADIAN, False),
    ('%sb', Language.AKKADIAN, False),
    ('%a', Language.AKKADIAN, False),
    ('%akk', Language.AKKADIAN, False),
    ('%eakk', Language.AKKADIAN, False),
    ('%oakk', Language.AKKADIAN, False),
    ('%ur3akk', Language.AKKADIAN, False),
    ('%oa', Language.AKKADIAN, False),
    ('%ob', Language.AKKADIAN, False),
    ('%sux', Language.SUMERIAN, False),
    ('%es', Language.EMESAL, False),
    ('%n', Language.AKKADIAN, True),
    ('%foo', DEFAULT_LANGUAGE, DEFAULT_NORMALIZED)
])
def test_line_of_iterable(code, language, normalized):
    prefix = '1.'
    tokens = [
        Word('first'),
        LanguageShift(code), Word('second'),
        LanguageShift('%sb'), Word('third')
    ]
    expected_tokens = (
        Word('first', DEFAULT_LANGUAGE, DEFAULT_NORMALIZED),
        LanguageShift(code), Word('second', language, normalized),
        LanguageShift('%sb'), Word('third', Language.AKKADIAN, False))
    line = TextLine.of_iterable(prefix, tokens)

    assert line == TextLine(prefix, expected_tokens)


def test_line_of_single():
    prefix = '$'
    token = Token('only')
    line = ControlLine.of_single(prefix, token)

    assert line == ControlLine('$', (token, ))


@pytest.mark.parametrize("line,expected", [
    (ControlLine.of_single('@', Token('obverse')), {
        'type': 'ControlLine',
        'prefix': '@',
        'content': [Token('obverse').to_dict()]
    }),
    (TextLine.of_iterable('1.', [Word('bu')]), {
        'type': 'TextLine',
        'prefix': '1.',
        'content': [Word('bu').to_dict()]
    }),
    (EmptyLine(), {
        'type': 'EmptyLine',
        'prefix': '',
        'content': []
    })
])
def test_to_dict(line, expected):
    assert line.to_dict() == expected

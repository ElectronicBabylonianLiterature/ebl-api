import pytest
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE
from ebl.fragmentarium.line import Line, TextLine, ControlLine
from ebl.fragmentarium.token import Token, Word, LanguageShift


def test_line():
    prefix = '1.'
    token = Token('value')
    line = Line(prefix, (token, ))

    assert line.prefix == prefix
    assert line.content == (token, )


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
def test_line_of_iterable(code, expected_language):
    prefix = '1.'
    tokens = [
        Word('first'),
        LanguageShift(code), Word('second'),
        LanguageShift('%sb'), Word('third')
    ]
    expected_tokens = (
        Word('first', DEFAULT_LANGUAGE),
        LanguageShift(code), Word('second', expected_language),
        LanguageShift('%sb'), Word('third', Language.AKKADIAN))
    line = TextLine.of_iterable(prefix, tokens)

    assert line == TextLine(prefix, expected_tokens)


def test_line_of_single():
    prefix = '$'
    token = Token('only')
    line = ControlLine.of_single(prefix, token)

    assert line == ControlLine('$', (token, ))

import pytest
from parsy import ParseError

from ebl.text.reconstructed_text_parser import AKKADIAN_WORD


@pytest.mark.parametrize('text,expected', [
    ('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ',
     ['abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ']),
    ('ibnû?', ['ibnû', '?']),
    ('ibnû#', ['ibnû', '#']),
    ('ibnû#?', ['ibnû', '#?']),
    ('ibnû?#', ['ibnû', '?#']),
    ('[ibnû]', ['[', 'ibnû', ']']),
    ('ib[nû', ['ib[nû']),
    ('ib]nû', ['ib]nû']),
    ('i[b]nû', ['i[b]nû']),
    ('ibnû?]', ['ibnû', '?', ']']),
    ('(ibnû)', ['(', 'ibnû', ')']),
    ('ib(nû', ['ib(nû']),
    ('ib)nû', ['ib)nû']),
    ('i(b)nû', ['i(b)nû']),
    ('ibnû#)', ['ibnû', '#', ')']),
    ('[(ibnû)]', ['[(', 'ibnû', ')]']),
    ('ib[(nû', ['ib[(nû']),
    ('ib)]nû', ['ib)]nû']),
    ('i[(b)]nû', ['i[(b)]nû']),
    ('[i(b)n]û', ['[', 'i(b)n]û']),
    ('ibnû?)]', ['ibnû', '?', ')]']),
])
def test_word(text, expected):
    assert [token for token in AKKADIAN_WORD.parse(text) if token] == expected


@pytest.mark.parametrize('text', [
    'x', 'KUR',
    'ibnû!', 'ibnû?#?',
    ']ibnû', 'ibnû[', '[[ibnû',
    ')ibnû', 'ibnû(', '((ibnû',
    'i([bnû', 'i])bnû', 'i[)]bnû',
    'ibnû?[#', 'ibnû#)?',
    'ibnû]?', 'ibnû)#', 'ibnû)]?'

])
def test_invalid_word(text):
    with pytest.raises(ParseError):
        AKKADIAN_WORD.parse(text)

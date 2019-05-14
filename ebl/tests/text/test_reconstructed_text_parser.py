import pytest
from parsy import ParseError

from ebl.text.reconstructed_text_parser import AKKADIAN_WORD, LACUNA, \
    CAESURA, FEET_SEPARATOR, Modifier, BrokenOffOpen, BrokenOffClose


def assert_parse(parser, expected, text):
    assert [token for token in parser.parse(text) if token] == expected


def assert_parse_error(parser, text):
    with pytest.raises(ParseError):
        parser.parse(text)


@pytest.mark.parametrize('text,expected', [
    ('abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ',
     ['abcdefghiklmnopqrstuwyzâêîûāēīšūṣṭʾ']),
    ('ibnû?', ['ibnû', [Modifier.UNCERTAIN]]),
    ('ibnû#', ['ibnû', [Modifier.BROKEN]]),
    ('ibnû#?', ['ibnû', [Modifier.BROKEN, Modifier.UNCERTAIN]]),
    ('ibnû?#', ['ibnû', [Modifier.UNCERTAIN, Modifier.BROKEN]]),
    ('[ibnû]', [BrokenOffOpen.BROKEN, 'ibnû', BrokenOffClose.BROKEN]),
    ('ib[nû', ['ib[nû']),
    ('ib]nû', ['ib]nû']),
    ('i[b]nû', ['i[b]nû']),
    ('ibnû?]', ['ibnû', [Modifier.UNCERTAIN], BrokenOffClose.BROKEN]),
    ('(ibnû)', [BrokenOffOpen.MAYBE, 'ibnû', BrokenOffClose.MAYBE]),
    ('ib(nû', ['ib(nû']),
    ('ib)nû', ['ib)nû']),
    ('i(b)nû', ['i(b)nû']),
    ('ibnû#)', ['ibnû', [Modifier.BROKEN], BrokenOffClose.MAYBE]),
    ('[(ibnû)]', [BrokenOffOpen.BOTH, 'ibnû', BrokenOffClose.BOTH]),
    ('ib[(nû', ['ib[(nû']),
    ('ib)]nû', ['ib)]nû']),
    ('i[(b)]nû', ['i[(b)]nû']),
    ('[i(b)n]û', [BrokenOffOpen.BROKEN, 'i(b)n]û']),
    ('ibnû?)]', ['ibnû', [Modifier.UNCERTAIN], BrokenOffClose.BOTH])
])
def test_word(text, expected):
    assert_parse(AKKADIAN_WORD, expected, text)


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
    assert_parse_error(AKKADIAN_WORD, text)


@pytest.mark.parametrize('text,expected', [
    ('...', ['...']),
    ('[...', [BrokenOffOpen.BROKEN, '...']),
    ('...]', ['...', BrokenOffClose.BROKEN]),
    ('[...]', [BrokenOffOpen.BROKEN, '...', BrokenOffClose.BROKEN]),
    ('(...', [BrokenOffOpen.MAYBE, '...']),
    ('...)', ['...', BrokenOffClose.MAYBE]),
    ('(...)', [BrokenOffOpen.MAYBE, '...', BrokenOffClose.MAYBE]),
    ('[(...', [BrokenOffOpen.BOTH, '...']),
    ('...)]', ['...', BrokenOffClose.BOTH]),
    ('[(...)]', [BrokenOffOpen.BOTH, '...', BrokenOffClose.BOTH])
])
def test_lacuna(text, expected):
    assert_parse(LACUNA, expected, text)


@pytest.mark.parametrize('text', [
    '.', '..', '....', '......'
    ']...', '...[', '[[...',
    ')...', '...(', '...))',
    '([...', '...])',
    '.)..', '..].', '..[(.'
    '...?', '...#',


])
def test_invalid_lacuna(text):
    assert_parse_error(LACUNA, text)


@pytest.mark.parametrize('text,expected', [
    ('||', '||'),
    ('(||)', '(||)')
])
def test_caesura(text, expected):
    assert CAESURA.parse(text) == expected


@pytest.mark.parametrize('text', [
    '|', '|||', '||||',
    '[||]', '[(||)]'
])
def test_invalid_caesura(text):
    assert_parse_error(CAESURA, text)


@pytest.mark.parametrize('text,expected', [
    ('|', '|'),
    ('(|)', '(|)')
])
def test_feet_separator(text, expected):
    assert FEET_SEPARATOR.parse(text) == expected


@pytest.mark.parametrize('text', [
    '||', '|||',
    '[|]', '[(|)]'
])
def test_invalid_feet_separator(text):
    assert_parse_error(FEET_SEPARATOR, text)

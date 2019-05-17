import pytest
from parsy import ParseError

from ebl.text.reconstructed_text_parser import AKKADIAN_WORD, LACUNA, \
    CAESURA, FOOT_SEPARATOR, RECONSTRUCTED_LINE
from ebl.text.reconstructed_text import Modifier, BrokenOffOpen, \
    BrokenOffClose, AkkadianWord, Lacuna, MetricalFootSeparator, Caesura, \
    StringPart, BrokenOffPart, validate


def assert_parse(parser, expected, text):
    assert [token for token in parser.parse(text) if token] == expected


def assert_parse_error(parser, text):
    with pytest.raises(ParseError):
        parser.parse(text)


@pytest.mark.parametrize('text,expected', [
    ('-ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄',
     [StringPart('-ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄'),
      []]),
    ('ibnû?', [StringPart('ibnû'), [Modifier.UNCERTAIN]]),
    ('ibnû#', [StringPart('ibnû'), [Modifier.BROKEN]]),
    ('ibnû#?', [StringPart('ibnû'), [Modifier.BROKEN, Modifier.UNCERTAIN]]),
    ('ibnû?#', [StringPart('ibnû'), [Modifier.UNCERTAIN, Modifier.BROKEN]]),
    ('[ibnû]', [BrokenOffPart(BrokenOffOpen.BROKEN), StringPart('ibnû'),
                BrokenOffPart(BrokenOffClose.BROKEN), []]),
    ('ib[nû', [StringPart('ib'), BrokenOffPart(BrokenOffOpen.BROKEN),
               StringPart('nû'), []]),
    ('ib]nû', [StringPart('ib'), BrokenOffPart(BrokenOffClose.BROKEN),
               StringPart('nû'), []]),
    ('i[b]nû', [StringPart('i'), BrokenOffPart(BrokenOffOpen.BROKEN),
                StringPart('b'), BrokenOffPart(BrokenOffClose.BROKEN),
                StringPart('nû'), []]),
    ('ibnû?]', [StringPart('ibnû'), BrokenOffPart(BrokenOffClose.BROKEN),
                [Modifier.UNCERTAIN]]),
    ('(ibnû)', [BrokenOffPart(BrokenOffOpen.MAYBE), StringPart('ibnû'),
                BrokenOffPart(BrokenOffClose.MAYBE), []]),
    ('ib(nû', [StringPart('ib'), BrokenOffPart(BrokenOffOpen.MAYBE),
               StringPart('nû'), []]),
    ('ib)nû', [StringPart('ib'), BrokenOffPart(BrokenOffClose.MAYBE),
               StringPart('nû'), []]),
    ('i(b)nû', [StringPart('i'), BrokenOffPart(BrokenOffOpen.MAYBE),
                StringPart('b'), BrokenOffPart(BrokenOffClose.MAYBE),
                StringPart('nû'), []]),
    ('ibnû#)', [StringPart('ibnû'), BrokenOffPart(BrokenOffClose.MAYBE),
                [Modifier.BROKEN]]),
    ('[(ibnû)]', [BrokenOffPart(BrokenOffOpen.BOTH), StringPart('ibnû'),
                  BrokenOffPart(BrokenOffClose.BOTH), []]),
    ('ib[(nû', [StringPart('ib'), BrokenOffPart(BrokenOffOpen.BOTH),
                StringPart('nû'), []]),
    ('ib)]nû', [StringPart('ib'), BrokenOffPart(BrokenOffClose.BOTH),
                StringPart('nû'), []]),
    ('i[(b)]nû', [StringPart('i'), BrokenOffPart(BrokenOffOpen.BOTH),
                  StringPart('b'), BrokenOffPart(BrokenOffClose.BOTH),
                  StringPart('nû'), []]),
    ('[i(b)n]û', [BrokenOffPart(BrokenOffOpen.BROKEN), StringPart('i'),
                  BrokenOffPart(BrokenOffOpen.MAYBE), StringPart('b'),
                  BrokenOffPart(BrokenOffClose.MAYBE), StringPart('n'),
                  BrokenOffPart(BrokenOffClose.BROKEN), StringPart('û'), []]),
    ('ibnû?)]', [StringPart('ibnû'), BrokenOffPart(BrokenOffClose.BOTH),
                 [Modifier.UNCERTAIN]])
])
def test_word(text, expected):
    assert AKKADIAN_WORD.parse(text) == expected


@pytest.mark.parametrize('text', [
    'x', 'KUR',
    'ibnû!', 'ibnû?#?',
    ']ibnû', 'ibnû[', '[[ibnû',
    ')ibnû', 'ibnû(', '((ibnû',
    'i([bnû', 'i])bnû', 'i[)]bnû', 'i[b][n]û', 'ib[]nû'
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
    assert FOOT_SEPARATOR.parse(text) == expected


@pytest.mark.parametrize('text', [
    '||', '|||',
    '[|]', '[(|)]'
])
def test_invalid_feet_separator(text):
    assert_parse_error(FOOT_SEPARATOR, text)


WORD = AkkadianWord((StringPart('ibnû'),))


@pytest.mark.parametrize('text,expected', [
    ('ibnû', [WORD]),
    ('...', [Lacuna((None, None))]),
    ('ibnû | ibnû', [WORD, MetricalFootSeparator(False), WORD]),
    ('ibnû (|) ibnû', [WORD, MetricalFootSeparator(True), WORD]),
    ('ibnû || ibnû', [WORD, Caesura(False), WORD]),
    ('ibnû (||) ibnû', [WORD, Caesura(True), WORD]),
])
def test_reconstructed_line(text, expected):
    assert RECONSTRUCTED_LINE.parse(text) == expected


@pytest.mark.parametrize('text', [
    '|', '(|)', '||', '(||)', '| ||',
    'ibnû (|)', '|| ibnû', '... (||)', '(|) ...',
    'ibnû | | ibnû', 'ibnû | || ibnû'
])
def test_invalid_reconstructed_line(text):
    assert_parse_error(RECONSTRUCTED_LINE, text)


@pytest.mark.parametrize('text', [
    '[ibnû', '(ibnû', '[(ibnû',
    'ibnû]', 'ibnû)', 'ibnû)]'
    '[ibnû)]', '[(ibnû]'
    '[... [ibnû] ...]', '[(... [ibnû] ...)]', '[(... (ibnû) ...)]'
])
def test_validate(text):
    line = RECONSTRUCTED_LINE.parse(text)
    with pytest.raises(ValueError):
        validate(line)

import re
import pydash
from parsy import string, regex, seq, ParseError
from ebl.text.atf import AtfSyntaxError
from ebl.text.line import EmptyLine, TextLine, ControlLine
from ebl.text.text import Text
from ebl.text.token import Token, Word, LanguageShift


LINE_NUMBER = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
TABULATION = regex(r'\(\$___\$\)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column')
DIVIDER = regex(r'\||:|;|/').desc('divider')
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
LACUNA = regex(r'\[?\.\.\.\]?').desc('lacuna')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
WORD = regex(r'[^\s]+').desc('word')


WORD_SEPARATOR = string(' ').desc('word separtor')
LINE_SEPARATOR = regex(r'\n').desc('line separator')


CONTROL_LINE = seq(
    regex(r'(=:|\$|@|&|#)'),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)
EMPTY_LINE = regex(
    r'^$', re.RegexFlag.MULTILINE
).map(lambda _: EmptyLine()) << LINE_SEPARATOR
TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    (
        TABULATION.map(Token) |
        COLUMN.map(Token) |
        DIVIDER.map(Token) |
        COMMENTARY_PROTOCOL.map(Token) |
        LACUNA.map(Token) |
        SHIFT.map(LanguageShift) |
        WORD.map(Word)
    ).many().sep_by(WORD_SEPARATOR).map(pydash.flatten)
).combine(TextLine.of_iterable)


ATF = (
    (CONTROL_LINE | TEXT_LINE | EMPTY_LINE)
    .many()
    .sep_by(LINE_SEPARATOR)
    .map(pydash.flatten)
    .map(tuple)
    .map(Text)
)


def parse_atf(atf: str):
    try:
        return ATF.parse(atf)
    except ParseError as error:
        line_number = int(error.line_info().split(':')[0]) + 1
        raise AtfSyntaxError(line_number)

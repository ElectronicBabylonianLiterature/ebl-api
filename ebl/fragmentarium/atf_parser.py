import re
import pydash
from parsy import string, regex, seq, generate
from ebl.fragmentarium.language import Language
from ebl.fragmentarium.text import (
    EmptyLine, TextLine, ControlLine, Token, Word, LanguageShift
)


DEFAULT_LANGUAGE = Language.AKKADIAN


LINE_NUMBER = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
TABULATION = regex(r'\(\$___\$\)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column')
DIVIDER = regex(r'\||:|;|/').desc('divider')
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
LACUNA = regex(r'\[?\.\.\.\]?').desc('lacuna')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
WORD = regex(r'[^\s]+').desc('word')


WORD_SEPARATOR = string(' ').many().concat().desc('word separtor')
LINE_SEPARATOR = regex(r'\n').desc('line separator')


@generate('text content')
def text_content():
    language = DEFAULT_LANGUAGE
    generic_token = (
        TABULATION |
        COLUMN |
        DIVIDER |
        COMMENTARY_PROTOCOL |
        LACUNA
    )
    text_part = ((
        generic_token.map(Token) |
        SHIFT.map(LanguageShift) |
        WORD.map(lambda value: Word(value, language))
    ) << WORD_SEPARATOR).optional()

    tokens = []
    token = yield text_part
    while token is not None:
        tokens.append(token)
        if (
                isinstance(token, LanguageShift) and
                token.language is not Language.UNKNOWN
        ):
            language = token.language
        token = yield text_part

    return tokens


CONTROL_LINE = seq(
    regex(r'(=:|\$|@|&|#)'),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)
EMPTY_LINE = regex(
    '^$', re.RegexFlag.MULTILINE
).map(lambda _: EmptyLine()) << LINE_SEPARATOR
TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    text_content
).combine(TextLine.of_iterable)


ATF = (CONTROL_LINE | TEXT_LINE | EMPTY_LINE).many().sep_by(LINE_SEPARATOR)


def parse_atf(input_: str):
    return pydash.flatten(ATF.parse(input_))

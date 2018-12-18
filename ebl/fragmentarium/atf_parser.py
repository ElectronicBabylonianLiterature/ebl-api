import re
import pydash
from parsy import string, regex, seq, generate
from ebl.fragmentarium.language import Language
from ebl.fragmentarium.text import (
    EmptyLine, TextLine, ControlLine, Token, Word, Shift
)


def parse_atf(input_: str):
    # pylint: disable=R0914
    tabulation = regex(r'\(\$___\$\)').map(Token).desc('tabulation')
    column = regex(r'&\d*').map(Token).desc('column')
    divider = regex(r'\||:|;|/').map(Token).desc('divider')
    commentary_protocol =\
        regex(r'!(qt|bs|cm|zz)').map(Token).desc('commentary protocol')
    shift = (
        regex(r'%\w+')
        .map(Shift)
        .desc('language or register/writing system shift')
    )
    line_number = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
    lacuna = regex(r'\[?\.\.\.\]?').map(Token).desc('lacuna')
    word = regex(r'[^\s]+').desc('word')

    word_separator = string(' ').desc('word separtor')
    line_separator = regex(r'\n').desc('line separator')

    control_line = seq(
        regex(r'(=:|\$|@|&|#)'),
        regex(r'.*').map(Token)
    ).combine(ControlLine.of_single)
    empty_line = regex(
        '^$', re.RegexFlag.MULTILINE
    ).map(lambda _: EmptyLine()) << line_separator

    @generate('text content')
    def text_content():
        default_language = Language.AKKADIAN
        language = default_language

        text_part = ((
            tabulation |
            column |
            divider |
            commentary_protocol |
            shift |
            lacuna |
            word.map(lambda value: Word(value, language))
        ) << word_separator.many()).optional()

        tokens = []
        token = yield text_part
        while token is not None:
            tokens.append(token)
            if (
                    isinstance(token, Shift) and
                    token.language is not Language.UNKNOWN
            ):
                language = token.language
            token = yield text_part

        return tokens

    text_line = seq(
        line_number << word_separator,
        text_content
    ).combine(TextLine.of_iterable)

    atf = (control_line | text_line | empty_line).many().sep_by(line_separator)

    return pydash.flatten(atf.parse(input_))

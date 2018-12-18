import re
import pydash
from parsy import string, regex, seq
from ebl.fragmentarium.text import (
    EmptyLine, TextLine, ControlLine, Token, Word, Shift
)


def tokenize(input_: str):
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
    word = regex(r'[^\s]+').map(Word).desc('word')

    word_separator = string(' ').desc('word separtor')
    line_separator = regex(r'\n').desc('line separator')

    text = (
        tabulation |
        column |
        divider |
        commentary_protocol |
        shift |
        lacuna |
        word
    ).many().sep_by(word_separator).map(pydash.flatten)

    control_line = seq(
        regex(r'(=:|\$|@|&|#)'),
        regex(r'.*').map(Token)
    ).combine(ControlLine.of_single)
    text_line =\
        seq(line_number << word_separator, text).combine(TextLine.of_iterable)
    empty_line = regex(
        '^$', re.RegexFlag.MULTILINE
    ).map(lambda _: EmptyLine()) << line_separator

    atf = (control_line | text_line | empty_line).many().sep_by(line_separator)

    return pydash.flatten(atf.parse(input_))

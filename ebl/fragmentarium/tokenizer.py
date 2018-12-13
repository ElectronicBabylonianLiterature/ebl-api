import re
import typing
import attr
import pydash
from parsy import string, regex, seq, any_char, generate
from ebl.fragmentarium.tokens import Token, Word, Shift


@attr.s(auto_attribs=True)
class Line:
    number: str = ''
    content: typing.List[Token] = attr.Factory(list)


@attr.s(auto_attribs=True)
class ControlLine:
    prefix: str = ''
    content: str = ''


@attr.s
class EmptyLine:
    def __eq__(self, other):
        return isinstance(other, EmptyLine)


def tokenize(input_: str):
    tabulation = regex(r'\(\$___\$\)').map(Token).desc('tabulation')
    column = regex(r'&\d*').map(Token).desc('column')
    divider = regex(r'\||:|;|/').map(Token).desc('divider')
    commentary_protocol =\
        regex(r'!(qt|bs|cm|zz)').map(Token).desc('commentary protocol')
    unclear = string('x').map(Token).desc('unclear sign')
    unidentified = string('X').map(Token).desc('unindentified sign')
    shift = (
        regex(r'%\w+')
        .map(Shift)
        .desc('language or register/writing system shift')
    )
    line_number = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
    lacuna = string('...').map(Token).desc('lacuna')
    word = regex(r'[^\s]+').map(Word).desc('word')

    word_separator = string(' ').desc('word separtor')
    line_separator = regex(r'\n').desc('line separator')

    text = (
        tabulation |
        column |
        divider |
        commentary_protocol |
        unclear |
        unidentified |
        shift |
        lacuna |
        word
    ).many().sep_by(word_separator).map(pydash.flatten)

    control_line = seq(
        regex(r'(=:|\$|@|&|#)'),
        regex(r'.*')
    ).combine(ControlLine)
    text_line = seq(line_number << word_separator, text).combine(Line)
    empty_line = regex(
        '^$', re.RegexFlag.MULTILINE
    ).map(lambda _: EmptyLine()) << line_separator

    atf = (control_line | text_line | empty_line).many().sep_by(line_separator)

    return pydash.flatten(atf.parse(input_))

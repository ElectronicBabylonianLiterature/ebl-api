import re

import pydash
from parsy import (ParseError, regex, seq)

import ebl.text.atf
from ebl.text.line import ControlLine, EmptyLine
from ebl.text.text import Text
from ebl.text.text_parser import TEXT_LINE
from ebl.text.token import Token


LINE_SEPARATOR = regex(r'\n').desc('line separator')

CONTROL_LINE = seq(
    regex(r'^(=:|\$|@|&|#)', re.RegexFlag.MULTILINE),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)

EMPTY_LINE = regex(
    r'^$', re.RegexFlag.MULTILINE
).map(lambda _: EmptyLine()) << LINE_SEPARATOR

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
        raise ebl.text.atf.AtfSyntaxError(line_number)

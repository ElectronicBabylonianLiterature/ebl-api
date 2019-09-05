import re

import pydash
from parsy import ParseError, regex, seq

from ebl.text.atf import ATF_PARSER_VERSION, Atf
from ebl.text.line import ControlLine, EmptyLine
from ebl.text.text import Text
from ebl.text.text_parser import TEXT_LINE
from ebl.text.token import Token
from ebl.text.transliteration_error import TransliterationError

CONTROL_LINE = seq(
    regex(r'^(=:|\$|@|&|#)', re.RegexFlag.MULTILINE),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)

EMPTY_LINE = regex(
    r'^\s*$'
).map(lambda _: EmptyLine())

LINE = CONTROL_LINE | TEXT_LINE | EMPTY_LINE


def parse_atf(atf: Atf):
    def parse_line(line: str, line_number: int):
        try:
            return (LINE.parse(line), None)
        except ParseError:
            return (None,  {
                'description': 'Invalid line',
                'lineNumber': line_number + 1
            })

    def check_errors(pairs):
        errors = [
            error
            for line, error in pairs
            if error is not None
        ]
        if any(errors):
            raise TransliterationError(errors)

    lines = tuple(pydash
                  .chain(atf)
                  .split('\n')
                  .map(parse_line)
                  .tap(check_errors)
                  .map(lambda pair: pair[0])
                  .drop_right_while(lambda line: line.prefix == '')
                  .value())

    return Text(lines, ATF_PARSER_VERSION)

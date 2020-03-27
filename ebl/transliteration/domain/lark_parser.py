from collections import Counter
from itertools import dropwhile
from typing import Sequence

from lark.lark import Lark
from lark.exceptions import ParseError, UnexpectedInput, VisitError, LarkError
from lark.visitors import v_args

from ebl.errors import DataError
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line_transformer import AtLineTransformer
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransfomer
from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureValidator
from ebl.transliteration.domain.labels import DuplicateStatusError
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
)
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.tokens import ValueToken, Token as EblToken
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import Word


class LineTransformer(
    AtLineTransformer, DollarLineTransfomer, NoteLineTransformer, TextLineTransformer
):
    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine.of_single(prefix, ValueToken.of(content))


WORD_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="any_word"
)
LINE_PARSER = Lark.open("ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)


def parse_word(atf: str) -> Word:
    tree = WORD_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_erasure(atf: str) -> Sequence[EblToken]:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__erasure")
    return LineTransformer().transform(tree)


def parse_line(atf: str) -> Line:
    tree = LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def validate_line(line: Line) -> None:
    visitor = EnclosureValidator()
    for token in line.content:
        token.accept(visitor)
    visitor.done()


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            parsed_line = parse_line(line) if line else EmptyLine()
            validate_line(parsed_line)
            return parsed_line, None
        except (UnexpectedInput, ParseError, EnclosureError, VisitError) as ex:
            return (None, create_transliteration_error_data(ex, line, line_number))

    def check_errors(pairs):
        errors = [error for line, error in pairs if error is not None]
        if any(errors):
            raise TransliterationError(errors)

    lines = atf_.split("\n")
    lines = list(dropwhile(lambda line: line == "", reversed(lines)))
    lines.reverse()
    lines = [parse_line_(line, number)
             for number, line
             in enumerate(lines)]
    check_errors(lines)
    lines = tuple(pair[0] for pair in lines)

    text = Text(lines, f"{atf.ATF_PARSER_VERSION}")

    if any(count > 1 for count in Counter(text.labels).values()):
        raise DataError("Duplicate labels.")

    return text


def create_transliteration_error_data(error, line: str, line_number: int):
    handlers = {
        UnexpectedInput: unexpected_input_error,
        ParseError: parse_error,
        EnclosureError: enclosure_error,
        VisitError: visit_error,
    }
    for type_ in handlers:
        if isinstance(error, type_):
            return handlers[type_](error, line, line_number) 

    raise error


def unexpected_input_error(error: UnexpectedInput, line: str, line_number: int):
    description = "Invalid line: "
    context = error.get_context(line, 6).split("\n", 1)
    return {
        "description": (
            description + context[0] + "\n" + len(description) * " " + context[1]
        ),
        "lineNumber": line_number + 1,
    }


def parse_error(error: ParseError, line: str, line_number: int):
    return {"description": f"Invalid line: {error}", "lineNumber": line_number + 1}


def enclosure_error(error: EnclosureError, line: str, line_number: int):
    return {"description": f"Invalid brackets.", "lineNumber": line_number + 1}


def visit_error(error: VisitError, line: str, line_number: int):
    if isinstance(error.orig_exc, DuplicateStatusError):  # type: ignore
        return {"description": f"Duplicate Status", "lineNumber": line_number + 1}
    else:
        raise error

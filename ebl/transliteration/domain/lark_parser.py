from itertools import dropwhile
from typing import Any, Callable, Mapping, Sequence, Tuple, Type, Union

from lark.exceptions import ParseError, UnexpectedInput, VisitError  # pyre-ignore[21]
from lark.lark import Lark  # pyre-ignore[21]
from lark.visitors import v_args  # pyre-ignore[21]
import pydash  # pyre-ignore[21]

from ebl.errors import DataError
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line_transformer import AtLineTransformer
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.dollar_line_transformer import DollarLineTransfomer
from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureValidator
from ebl.transliteration.domain.greek_tokens import GreekWord
from ebl.transliteration.domain.labels import DuplicateStatusError
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.note_line_transformer import NoteLineTransformer
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.parallel_line_transformer import ParallelLineTransformer
from ebl.transliteration.domain.sign_tokens import CompoundGrapheme
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.tokens import Token as EblToken
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import Word


PARSE_ERRORS: Tuple[Type[Any], ...] = (
    UnexpectedInput,
    ParseError,
    VisitError,
    EnclosureError,
)


class LineTransformer(
    AtLineTransformer,
    DollarLineTransfomer,
    NoteLineTransformer,
    TextLineTransformer,
    ParallelLineTransformer,
):
    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine(prefix, content)


WORD_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="any_word"
)
NOTE_LINE_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="note_line"
)
PARALLEL_LINE_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="parallel_line"
)
PARATEXT_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="paratext"
)
LINE_PARSER = Lark.open("ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)


def parse_word(atf: str) -> Word:
    tree = WORD_PARSER.parse(atf)
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_normalized_akkadian_word(atf: str) -> Word:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__akkadian_word")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_greek_word(atf: str) -> GreekWord:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__greek_word")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_compound_grapheme(atf: str) -> CompoundGrapheme:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__compound_grapheme")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_erasure(atf: str) -> Sequence[EblToken]:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__erasure")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_line(atf: str) -> Line:
    tree = LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_note_line(atf: str) -> NoteLine:
    tree = NOTE_LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_parallel_line(atf: str) -> ParallelLine:
    tree = PARALLEL_LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_text_line(atf: str) -> TextLine:
    tree = LINE_PARSER.parse(atf, start="text_line")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_paratext(atf: str) -> Union[NoteLine, DollarLine]:
    tree = PARATEXT_PARSER.parse(atf)
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def parse_line_number(atf: str) -> AbstractLineNumber:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__line_number")
    return LineTransformer().transform(tree)  # pyre-ignore[16]


def validate_line(line: Line) -> None:
    visitor = EnclosureValidator()
    line.accept(visitor)
    visitor.done()


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            parsed_line = parse_line(line) if line else EmptyLine()
            validate_line(parsed_line)
            return parsed_line, None
        except PARSE_ERRORS as ex:
            return (None, create_transliteration_error_data(ex, line, line_number))

    def check_errors(pairs):
        errors = [error for line, error in pairs if error is not None]
        if any(errors):
            raise TransliterationError(errors)

    lines = atf_.split("\n")
    lines = list(dropwhile(lambda line: line == "", reversed(lines)))
    lines.reverse()
    lines = [parse_line_(line, number) for number, line in enumerate(lines)]
    check_errors(lines)
    lines = tuple(pair[0] for pair in lines)

    text = Text(lines, f"{atf.ATF_PARSER_VERSION}")

    if pydash.duplicates(text.labels):
        raise DataError("Duplicate labels.")
    else:
        return text


def create_transliteration_error_data(error: Exception, line: str, line_number: int):
    handlers: Mapping[Type, Callable[[Exception, str, int], dict]] = {
        UnexpectedInput: unexpected_input_error,
        ParseError: parse_error,
        EnclosureError: enclosure_error,
        VisitError: visit_error,
    }
    for type_ in handlers:
        if isinstance(error, type_):
            return handlers[type_](error, line, line_number)

    raise error


def unexpected_input_error(
    error: UnexpectedInput, line: str, line_number: int  # pyre-ignore[11]
):
    description = "Invalid line: "
    context = error.get_context(line, 6).split("\n", 1)
    return {
        "description": (
            description + context[0] + "\n" + len(description) * " " + context[1]
        ),
        "lineNumber": line_number + 1,
    }


def parse_error(error: ParseError, line: str, line_number: int):  # pyre-ignore[11]
    return {"description": f"Invalid line: {error}", "lineNumber": line_number + 1}


def enclosure_error(error: EnclosureError, line: str, line_number: int):
    return {"description": "Invalid brackets.", "lineNumber": line_number + 1}


def visit_error(error: VisitError, line: str, line_number: int):  # pyre-ignore[11]
    if isinstance(error.orig_exc, DuplicateStatusError):  # type: ignore
        return {"description": "Duplicate Status", "lineNumber": line_number + 1}
    else:
        raise error

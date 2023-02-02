from itertools import dropwhile
from typing import Sequence, Iterator
import re

import pydash
from lark.exceptions import ParseError, UnexpectedInput, VisitError
from lark.lark import Lark

from ebl.errors import DataError
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureValidator
from ebl.transliteration.domain.greek_tokens import GreekWord
from ebl.transliteration.domain.labels import DuplicateStatusError
from ebl.transliteration.domain.line import EmptyLine, Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.markup import MarkupPart, ParagraphPart
from ebl.transliteration.domain.note_line import NoteLine

from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.sign_tokens import CompoundGrapheme, Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token as EblToken
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.line_transformer import LineTransformer

WORD_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="any_word"
)
NOTE_LINE_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="note_line"
)
MARKUP_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="markup"
)
PARALLEL_LINE_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="parallel_line"
)
TRANSLATION_LINE_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="translation_line"
)
PARATEXT_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="paratext"
)
CHAPTER_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="chapter"
)
LINE_PARSER = Lark.open("ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)


def parse_word(atf: str) -> Word:
    tree = WORD_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_normalized_akkadian_word(atf: str) -> Word:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__akkadian_word")
    return LineTransformer().transform(tree)


def parse_greek_word(atf: str) -> GreekWord:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__greek_word")
    return LineTransformer().transform(tree)


def parse_compound_grapheme(atf: str) -> CompoundGrapheme:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__compound_grapheme")
    return LineTransformer().transform(tree)


def parse_reading(atf: str) -> Reading:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__reading")
    return LineTransformer().transform(tree)


def parse_erasure(atf: str) -> Sequence[EblToken]:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__erasure")
    return LineTransformer().transform(tree)


def parse_line(atf: str) -> Line:
    tree = LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_note_line(atf: str) -> NoteLine:
    tree = NOTE_LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_markup(atf: str) -> Sequence[MarkupPart]:
    tree = MARKUP_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def split_paragraphs(atf: str) -> Iterator[str]:
    for paragraph in re.split(r"\n\n+", atf.strip()):
        yield " ".join(paragraph.split())


def parse_markup_paragraphs(atf: str) -> Sequence[MarkupPart]:
    parts = []
    for paragraph in split_paragraphs(atf):
        if parts:
            parts.append(ParagraphPart())
        parts.extend(LineTransformer().transform(MARKUP_PARSER.parse(paragraph)))
    return tuple(parts)


def parse_parallel_line(atf: str) -> ParallelLine:
    tree = PARALLEL_LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_translation_line(atf: str) -> TranslationLine:
    tree = TRANSLATION_LINE_PARSER.parse(atf)
    return LineTransformer().transform(tree)


def parse_text_line(atf: str) -> TextLine:
    tree = LINE_PARSER.parse(atf, start="text_line")
    return LineTransformer().transform(tree)


def parse_line_number(atf: str) -> AbstractLineNumber:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__line_number")
    return LineTransformer().transform(tree)


def validate_line(line: Line) -> None:
    visitor = EnclosureValidator()
    line.accept(visitor)
    visitor.done()


def clean_line(line: str):
    replacements = {"\t+": " ", " ̶": "-"}

    for old, new in replacements.items():
        line = re.sub(old, new, line)

    return line


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            line = clean_line(line)
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
    handlers = {
        UnexpectedInput: unexpected_input_error,
        ParseError: parse_error,
        EnclosureError: enclosure_error,
        VisitError: visit_error,
    }
    for type_, handler in handlers.items():
        if isinstance(error, type_):
            return handler(error, line, line_number)  # pyre-ignore[6]

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
    return {"description": "Invalid brackets.", "lineNumber": line_number + 1}


def visit_error(error: VisitError, line: str, line_number: int):
    if isinstance(error.orig_exc, DuplicateStatusError):
        return {"description": "Duplicate Status", "lineNumber": line_number + 1}
    else:
        raise error

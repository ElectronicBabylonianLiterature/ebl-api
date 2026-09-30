from functools import singledispatch
from typing import Tuple, Type

from lark.exceptions import ParseError, UnexpectedInput, VisitError

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.labels import DuplicateStatusError
from ebl.transliteration.domain.transliteration_error import (
    ErrorAnnotation,
    ExtentLabelError,
    TransliterationError,
)

PARSE_ERRORS: Tuple[Type[Exception], ...] = (
    UnexpectedInput,
    ParseError,
    VisitError,
    EnclosureError,
)

LINE_PARSE_ERRORS: Tuple[Type[Exception], ...] = (
    *PARSE_ERRORS,
    TransliterationError,
    ExtentLabelError,
)


@singledispatch
def create_transliteration_error_data(
    error: Exception, line: str, line_number: int
) -> ErrorAnnotation:
    raise error


@create_transliteration_error_data.register
def _(error: UnexpectedInput, line: str, line_number: int) -> ErrorAnnotation:
    description = "Invalid line: "
    context = error.get_context(line, 6).split("\n", 1)
    return ErrorAnnotation(
        description + context[0] + "\n" + len(description) * " " + context[1],
        line_number + 1,
    )


@create_transliteration_error_data.register
def _(error: ParseError, line: str, line_number: int) -> ErrorAnnotation:
    return ErrorAnnotation(f"Invalid line: {error}", line_number + 1)


@create_transliteration_error_data.register
def _(error: EnclosureError, line: str, line_number: int) -> ErrorAnnotation:
    return ErrorAnnotation("Invalid brackets.", line_number + 1)


@create_transliteration_error_data.register
def _(error: VisitError, line: str, line_number: int) -> ErrorAnnotation:
    if isinstance(error.orig_exc, DuplicateStatusError):
        return ErrorAnnotation("Duplicate Status", line_number + 1)
    else:
        raise error

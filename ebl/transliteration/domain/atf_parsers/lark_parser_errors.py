from lark.exceptions import ParseError, UnexpectedInput, VisitError
from ebl.transliteration.domain.enclosure_error import EnclosureError
from typing import Tuple, Type

PARSE_ERRORS: Tuple[Type[Exception], ...] = (
    UnexpectedInput,
    ParseError,
    VisitError,
    EnclosureError,
)

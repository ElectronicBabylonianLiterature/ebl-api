from enum import Enum, unique
from typing import Mapping, Sequence

import attr

from ebl.common.query.parameter_parser import (
    parse_limit,
    parse_non_negative_integer_field,
)
from ebl.errors import DataError

DEFAULT_LINES_OFFSET = 0
DEFAULT_LINES_LIMIT = 10
MAX_LINES_LIMIT = 50
MAX_LINES_OFFSET = 2**31 - 1
TOKENS_ENABLED = "true"
TOKENS_DISABLED = "false"
TOKENS_VALUES: Sequence[str] = (TOKENS_ENABLED, TOKENS_DISABLED)


@unique
class LinesView(Enum):
    CHAPTER = "chapter"
    OUTLINE = "outline"


@attr.s(frozen=True, auto_attribs=True)
class LinesPageQuery:
    offset: int = DEFAULT_LINES_OFFSET
    limit: int = DEFAULT_LINES_LIMIT
    include_tokens: bool = False


def _parse_offset(parameters: Mapping[str, object]) -> int:
    offset: int = parse_non_negative_integer_field("offset")(dict(parameters)).get(
        "offset", DEFAULT_LINES_OFFSET
    )
    if offset > MAX_LINES_OFFSET:
        raise DataError(
            f"offset must be at most {MAX_LINES_OFFSET}, got {offset} instead"
        )
    return offset


def _parse_limit(parameters: Mapping[str, object]) -> int:
    limit: int = parse_limit(dict(parameters)).get("limit", DEFAULT_LINES_LIMIT)
    return min(limit, MAX_LINES_LIMIT)


def _parse_tokens(parameters: Mapping[str, object]) -> bool:
    tokens = parameters.get("tokens", TOKENS_DISABLED)
    if tokens not in TOKENS_VALUES:
        raise DataError(
            f"tokens must be {TOKENS_ENABLED} or {TOKENS_DISABLED}, "
            f"got {tokens!r} instead"
        )
    return tokens == TOKENS_ENABLED


def parse_lines_page_query(parameters: Mapping[str, object]) -> LinesPageQuery:
    return LinesPageQuery(
        _parse_offset(parameters),
        _parse_limit(parameters),
        _parse_tokens(parameters),
    )


def parse_lines_view(parameters: Mapping[str, object]) -> LinesView:
    view = parameters.get("view", LinesView.CHAPTER.value)
    try:
        return LinesView(view)
    except ValueError as error:
        raise DataError(f"unexpected view {view!r}") from error

from enum import Enum
from typing import Type, TypeVar

import falcon
from falcon import Request

from ebl.sumerian_dictionary.domain.search_query import (
    DEFAULT_LIMIT,
    MAXIMUM_LIMIT,
    Kind,
    SourceFilter,
    SumerianWordQuery,
)

E = TypeVar("E", bound=Enum)


def _choice(req: Request, name: str, choices: Type[E], default: E) -> E:
    value = req.get_param(name)
    if not value:
        return default
    try:
        return choices(value)
    except ValueError as error:
        allowed = ", ".join(choice.value for choice in choices)
        raise falcon.HTTPInvalidParam(f"Expected one of: {allowed}.", name) from error


def _limit(req: Request) -> int:
    limit = req.get_param_as_int("limit", min_value=1) or DEFAULT_LIMIT
    return min(limit, MAXIMUM_LIMIT)


def parse_search_query(req: Request) -> SumerianWordQuery:
    return SumerianWordQuery(
        query=req.get_param("query") or "",
        kind=_choice(req, "kind", Kind, Kind.ALL),
        source=_choice(req, "source", SourceFilter, SourceFilter.ANY),
        limit=_limit(req),
        offset=req.get_param_as_int("offset", min_value=0) or 0,
    )

from typing import Dict, List, Optional, Union

import pytest

from ebl.corpus.application.lines_pagination import (
    DEFAULT_LINES_LIMIT,
    DEFAULT_LINES_OFFSET,
    MAX_LINES_LIMIT,
    MAX_LINES_OFFSET,
    LinesPageQuery,
    LinesView,
    parse_lines_page_query,
    parse_lines_view,
    parse_revision,
)
from ebl.errors import DataError

Parameters = Dict[str, Union[str, List[str]]]
REVISION = "6aff54f935de52a4db0c81df"


def test_limits() -> None:
    assert (
        DEFAULT_LINES_OFFSET,
        DEFAULT_LINES_LIMIT,
        MAX_LINES_LIMIT,
        MAX_LINES_OFFSET,
    ) == (0, 10, 50, 2147483647)


def test_parse_lines_page_query_defaults() -> None:
    assert parse_lines_page_query({}) == LinesPageQuery(0, 10, False)


def test_lines_page_query_defaults() -> None:
    assert LinesPageQuery() == LinesPageQuery(0, 10, False)


def test_parse_lines_page_query() -> None:
    parameters: Parameters = {"offset": "20", "limit": "25", "tokens": "true"}

    assert parse_lines_page_query(parameters) == LinesPageQuery(20, 25, True)


def test_parse_lines_page_query_with_revision() -> None:
    parameters: Parameters = {"offset": "20", "revision": REVISION}

    assert parse_lines_page_query(parameters) == LinesPageQuery(20, 10, False, REVISION)


def test_lines_page_query_has_no_revision_by_default() -> None:
    assert LinesPageQuery().revision is None
    assert parse_lines_page_query({"tokens": "true"}).revision is None


def test_parse_lines_page_query_ignores_other_parameters() -> None:
    assert parse_lines_page_query({"view": "outline", "lines": "3"}) == LinesPageQuery()


def test_parse_lines_page_query_does_not_change_parameters() -> None:
    parameters: Parameters = {"offset": "20", "limit": "500", "tokens": "false"}
    parse_lines_page_query(parameters)

    assert parameters == {"offset": "20", "limit": "500", "tokens": "false"}


@pytest.mark.parametrize(
    "offset,expected",
    [("0", 0), ("7", 7), (" 7 ", 7), (str(MAX_LINES_OFFSET), MAX_LINES_OFFSET)],
)
def test_parse_offset(offset: str, expected: int) -> None:
    assert parse_lines_page_query({"offset": offset}).offset == expected


@pytest.mark.parametrize(
    "limit,expected",
    [("1", 1), ("10", 10), ("50", 50), ("51", 50), ("200", 50), ("1000000", 50)],
)
def test_parse_limit(limit: str, expected: int) -> None:
    assert parse_lines_page_query({"limit": limit}).limit == expected


@pytest.mark.parametrize("tokens,expected", [("true", True), ("false", False)])
def test_parse_tokens(tokens: str, expected: bool) -> None:
    assert parse_lines_page_query({"tokens": tokens}).include_tokens is expected


@pytest.mark.parametrize(
    "parameters,message",
    [
        ({"offset": "abc"}, "offset must be integer, got 'abc' instead"),
        ({"offset": ""}, "offset must be integer, got '' instead"),
        ({"offset": "1.5"}, "offset must be integer, got '1.5' instead"),
        ({"offset": ["1", "2"]}, "offset must be integer, got ['1', '2'] instead"),
        ({"offset": "-1"}, "offset must be non-negative"),
        (
            {"offset": "2147483648"},
            "offset must be at most 2147483647, got 2147483648 instead",
        ),
        ({"offset": str(2**63)}, "offset exceeds the maximum supported integer"),
        ({"limit": "abc"}, "limit must be integer, got 'abc' instead"),
        ({"limit": ""}, "limit must be integer, got '' instead"),
        ({"limit": "2.5"}, "limit must be integer, got '2.5' instead"),
        ({"limit": ["1", "2"]}, "limit must be integer, got ['1', '2'] instead"),
        ({"limit": "0"}, "limit must be at least 1, got 0 instead"),
        ({"limit": "-3"}, "limit must be at least 1, got -3 instead"),
        ({"tokens": "yes"}, "tokens must be true or false, got 'yes' instead"),
        ({"tokens": "True"}, "tokens must be true or false, got 'True' instead"),
        ({"tokens": ""}, "tokens must be true or false, got '' instead"),
        (
            {"tokens": ["true", "false"]},
            "tokens must be true or false, got ['true', 'false'] instead",
        ),
        ({"revision": ""}, "revision must be a non-empty string, got '' instead"),
        (
            {"revision": ["a", "b"]},
            "revision must be a non-empty string, got ['a', 'b'] instead",
        ),
    ],
)
def test_parse_invalid_lines_page_query(parameters: Parameters, message: str) -> None:
    with pytest.raises(DataError) as error:
        parse_lines_page_query(parameters)

    assert str(error.value) == message


@pytest.mark.parametrize(
    "parameters,expected",
    [
        ({}, None),
        ({"offset": "3", "view": "outline"}, None),
        ({"revision": REVISION}, REVISION),
        ({"revision": "legacy"}, "legacy"),
        ({"revision": " "}, " "),
    ],
)
def test_parse_revision(parameters: Parameters, expected: Optional[str]) -> None:
    assert parse_revision(parameters) == expected


@pytest.mark.parametrize(
    "revision,message",
    [
        ("", "revision must be a non-empty string, got '' instead"),
        (["a", "b"], "revision must be a non-empty string, got ['a', 'b'] instead"),
        ([], "revision must be a non-empty string, got [] instead"),
    ],
)
def test_parse_invalid_revision(revision: Union[str, List[str]], message: str) -> None:
    with pytest.raises(DataError) as error:
        parse_revision({"revision": revision})

    assert str(error.value) == message


@pytest.mark.parametrize(
    "parameters,expected",
    [
        ({}, LinesView.CHAPTER),
        ({"offset": "3"}, LinesView.CHAPTER),
        ({"view": "chapter"}, LinesView.CHAPTER),
        ({"view": "outline"}, LinesView.OUTLINE),
    ],
)
def test_parse_lines_view(parameters: Parameters, expected: LinesView) -> None:
    assert parse_lines_view(parameters) is expected


@pytest.mark.parametrize(
    "view,message",
    [
        ("lines", "unexpected view 'lines'"),
        ("Outline", "unexpected view 'Outline'"),
        ("", "unexpected view ''"),
        (["outline", "chapter"], "unexpected view ['outline', 'chapter']"),
    ],
)
def test_parse_invalid_lines_view(view: Union[str, List[str]], message: str) -> None:
    with pytest.raises(DataError) as error:
        parse_lines_view({"view": view})

    assert str(error.value) == message

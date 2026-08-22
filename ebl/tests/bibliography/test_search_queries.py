"""The search-query patterns, extracted from `Bibliography` to be testable."""

import pytest

from ebl.bibliography.application.search_queries import (
    parse_author_year_and_title,
    parse_container_title_short_and_collection_number,
    parse_title_short_and_volume,
)


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Miccadei", {"author": "Miccadei", "year": None, "title": None}),
        ("Miccadei 2002", {"author": "Miccadei", "year": 2002, "title": None}),
        (
            "Miccadei 2002 Thyroid",
            {"author": "Miccadei", "year": 2002, "title": "Thyroid"},
        ),
        ("2002", {"author": None, "year": None, "title": None}),
    ],
)
def test_parse_author_year_and_title(query, expected):
    assert parse_author_year_and_title(query) == expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("ME 1", {"container_title_short": "ME", "collection_number": "1"}),
        ("ME", {"container_title_short": "ME", "collection_number": None}),
        (
            "ME 1 extra",
            {"container_title_short": None, "collection_number": None},
        ),
    ],
)
def test_parse_container_title_short_and_collection_number(query, expected):
    assert parse_container_title_short_and_collection_number(query) == expected


@pytest.mark.parametrize(
    "query,expected",
    [
        ("MARV 2", {"title_short": "MARV", "volume": "2"}),
        ("MARV", {"title_short": "MARV", "volume": None}),
        ("MARV 2 extra", {"title_short": None, "volume": None}),
    ],
)
def test_parse_title_short_and_volume(query, expected):
    assert parse_title_short_and_volume(query) == expected

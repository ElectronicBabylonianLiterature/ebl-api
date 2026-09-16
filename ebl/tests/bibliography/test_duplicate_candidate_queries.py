import re

from ebl.bibliography.infrastructure.duplicate_candidate_queries import (
    container_title_year_query,
    contributor_year_query,
    doi_query,
    duplicate_candidate_queries,
    first_contributor_family,
    identifier_pattern,
    series_query_from_entry,
    year_title_query,
)


def test_duplicate_candidate_query_builders_return_none_for_sparse_entries() -> None:
    assert contributor_year_query({}) is None
    assert year_title_query({"title": "No year"}) is None
    assert container_title_year_query({"container-title": "No year"}) is None
    assert first_contributor_family({"author": ["not a dict"]}) is None


def test_series_query_from_title_short_and_volume() -> None:
    assert series_query_from_entry({"title-short": "BE", "volume": "1"}) == {
        "title-short": "BE",
        "volume": "1",
    }


def test_duplicate_candidate_queries_prioritize_strong_identifiers() -> None:
    queries = duplicate_candidate_queries(
        {
            "type": "article-journal",
            "title": "A Duplicate Candidate",
            "author": [{"family": "George"}],
            "issued": {"date-parts": [[2003]]},
            "DOI": "10.123/abc",
            "ISBN": "978-0-306-40615-7",
            "ISSN": "1234-567X",
            "container-title": "Journal of Cuneiform Studies",
        }
    )

    assert "DOI" in queries[0]["$or"][0]
    assert "ISBN" in queries[1]["$or"][0]
    assert "ISSN" in queries[-1]["$or"][0]


def test_identifier_pattern_matches_formatted_identifier_variants() -> None:
    pattern = re.compile(identifier_pattern("9780306406157"))

    assert pattern.fullmatch("9780306406157")
    assert pattern.fullmatch("978-0-306-40615-7")
    assert pattern.fullmatch("978 0 306 40615 7")
    assert not pattern.fullmatch("978O306406157")


def test_doi_query_matches_case_insensitive_variants() -> None:
    query = doi_query(["10.123/abc"])
    regex = query["$or"][1]["DOI"]
    pattern = re.compile(regex["$regex"], re.IGNORECASE)

    assert regex["$options"] == "i"
    assert pattern.fullmatch("10.123/ABC")
    assert not pattern.fullmatch("prefix 10.123/ABC")

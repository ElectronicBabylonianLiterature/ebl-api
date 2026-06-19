from ebl.bibliography.infrastructure.duplicate_candidate_queries import (
    container_title_year_query,
    contributor_year_query,
    first_contributor_family,
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

import pytest

from ebl.bibliography.infrastructure.bibliography import (
    ACTIVE_BIBLIOGRAPHY_FILTER,
    MongoBibliographyRepository,
    author_year_title_match,
    bibliography_query_pipeline,
    join_reference_documents,
)
from ebl.bibliography.infrastructure.bibliography_queries import (
    server_owned_state_filter,
)


def test_join_reference_documents_pipeline() -> None:
    pipeline = join_reference_documents()

    assert pipeline[0]["$unwind"]["path"] == "$references"
    assert pipeline[-1]["$set"]["references"]["$filter"]["as"] == "reference"


def test_author_year_title_match_and_pipeline() -> None:
    match = author_year_title_match("George", 2003, "Gilgamesh")
    pipeline = bibliography_query_pipeline(match, "title")

    assert match["author.0.family"] == "George"
    assert match["issued.date-parts.0.0"] == {"$gte": 2003, "$lt": 2004}
    assert pipeline[0] == {"$match": {**match, **ACTIVE_BIBLIOGRAPHY_FILTER}}
    assert pipeline[2]["$sort"]["title"] == 1


def test_query_by_author_year_and_title_uses_title_sort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = object.__new__(MongoBibliographyRepository)
    seen = {}

    def fake_query(match, trailing_sort_field):
        seen["match"] = match
        seen["trailing_sort_field"] = trailing_sort_field
        return ["result"]

    monkeypatch.setattr(repository, "_query", fake_query)

    assert repository.query_by_author_year_and_title("George", 2003, "Gilgamesh") == [
        "result"
    ]
    assert seen["trailing_sort_field"] == "title"


def test_server_owned_state_filter_requires_absent_fields_to_stay_absent() -> None:
    assert server_owned_state_filter("Q30000024", {}) == {
        "_id": "Q30000024",
        "aliases": {"$exists": False},
        "citationKey": {"$exists": False},
        "deprecated": {"$exists": False},
        "redirectTo": {"$exists": False},
    }


def test_server_owned_state_filter_matches_stored_values_exactly() -> None:
    filter_ = server_owned_state_filter("Q30000024", {"citationKey": "dossin1967La"})

    assert filter_["citationKey"] == "dossin1967La"
    assert filter_["aliases"] == {"$exists": False}


def test_server_owned_state_filter_separates_a_stored_null_from_an_absent_field() -> (
    None
):
    filter_ = server_owned_state_filter("Q30000024", {"redirectTo": None})

    assert filter_["redirectTo"] == {"$type": "null"}

import re

import pydash
import pytest

from ebl.bibliography.infrastructure.bibliography import (
    doi_query,
    duplicate_candidate_queries,
    identifier_pattern,
)
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

COLLECTION = "bibliography"


def test_create(database, bibliography_repository, create_mongo_bibliography_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)

    assert (
        database[COLLECTION].find_one({"_id": bibliography_entry["id"]})
        == create_mongo_bibliography_entry()
    )


def test_create_duplicate(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography_repository.create(bibliography_entry)
    with pytest.raises(DuplicateError):
        bibliography_repository.create(bibliography_entry)


def test_find(database, bibliography_repository, create_mongo_bibliography_entry):
    bibliography_entry = BibliographyEntryFactory.build()
    mongo_entry_ = create_mongo_bibliography_entry(bibliography_entry)
    database[COLLECTION].insert_one(mongo_entry_)

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"])
        == bibliography_entry
    )


def test_entry_not_found(bibliography_repository):
    with pytest.raises(NotFoundError):
        bibliography_repository.query_by_id("not found")


def test_update(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    updated_entry = pydash.omit({**bibliography_entry, "title": "New Title"}, "PMID")
    bibliography_repository.create(bibliography_entry)
    bibliography_repository.update(updated_entry)

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"]) == updated_entry
    )


def test_update_not_found(bibliography_repository):
    bibliography_entry = BibliographyEntryFactory.build()
    with pytest.raises(NotFoundError):
        bibliography_repository.update(bibliography_entry)


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

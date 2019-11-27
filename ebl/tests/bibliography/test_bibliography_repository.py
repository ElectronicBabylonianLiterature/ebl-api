import pydash
import pytest

from ebl.errors import DuplicateError, NotFoundError


@pytest.fixture
def mongo_entry(bibliography_entry):
    return pydash.map_keys(
        bibliography_entry, lambda _, key: "_id" if key == "id" else key
    )


COLLECTION = "bibliography"


def test_create(database, bibliography_repository, bibliography_entry, mongo_entry):
    bibliography_repository.create(bibliography_entry)

    assert (
        database[COLLECTION].find_one({"_id": bibliography_entry["id"]}) == mongo_entry
    )


def test_create_duplicate(bibliography_repository, bibliography_entry):
    bibliography_repository.create(bibliography_entry)
    with pytest.raises(DuplicateError):
        bibliography_repository.create(bibliography_entry)


def test_find(database, bibliography_repository, bibliography_entry, mongo_entry):
    database[COLLECTION].insert_one(mongo_entry)

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"])
        == bibliography_entry
    )


def test_entry_not_found(bibliography_repository):
    with pytest.raises(NotFoundError):
        bibliography_repository.query_by_id("not found")


def test_update(bibliography_repository, bibliography_entry):
    updated_entry = pydash.omit({**bibliography_entry, "title": "New Title"}, "PMID")
    bibliography_repository.create(bibliography_entry)
    bibliography_repository.update(updated_entry)

    assert (
        bibliography_repository.query_by_id(bibliography_entry["id"]) == updated_entry
    )


def test_update_not_found(bibliography_repository, bibliography_entry):
    with pytest.raises(NotFoundError):
        bibliography_repository.update(bibliography_entry)

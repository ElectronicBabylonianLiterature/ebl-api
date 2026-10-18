import logging

import bson
import pytest
from bson import ObjectId
from pymongo.common import MAX_BSON_SIZE

CACHE_COLLECTION = "cache"


def test_set(database, mongo_cache_repository) -> None:
    mongo_cache_repository.set("test", {"data": "data"})

    inserted_text = database[CACHE_COLLECTION].find_one(
        {"cache_key": "test"}, projection={"_id": False, "cache_key": False}
    )
    assert inserted_text == {"data": "data"}


def _item_of_encoded_size(cache_key: str, size: int) -> dict:
    empty_size = len(
        bson.encode({"_id": ObjectId(), "cache_key": cache_key, "data": ""})
    )
    return {"data": "x" * (size - empty_size)}


def test_set_at_size_limit(database, mongo_cache_repository) -> None:
    mongo_cache_repository.set("test", _item_of_encoded_size("test", MAX_BSON_SIZE))

    assert database[CACHE_COLLECTION].count_documents({"cache_key": "test"}) == 1


@pytest.mark.parametrize("excess", [1, 32 * 1024])
def test_set_too_large(database, mongo_cache_repository, caplog, excess) -> None:
    item = _item_of_encoded_size("test", MAX_BSON_SIZE + excess)

    with caplog.at_level(logging.WARNING):
        mongo_cache_repository.set("test", item)

    assert database[CACHE_COLLECTION].count_documents({}) == 0
    assert (
        f"Not caching test: {MAX_BSON_SIZE + excess} bytes exceeds {MAX_BSON_SIZE}"
        in caplog.text
    )


def test_has(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"cache_key": "test", "data": "data"})
    assert mongo_cache_repository.has("test") is True


def test_get(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"cache_key": "test", "data": "data"})
    assert mongo_cache_repository.get("test") == {"data": "data"}


def test_delete(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"cache_key": "test", "data": "data"})
    mongo_cache_repository.delete("test")
    assert database[CACHE_COLLECTION].find_one({"cache_key": "test"}) is None


@pytest.mark.parametrize(
    "key,expected", [("test", True), ("test line-42", True), ("foobar", False)]
)
def test_exists_with_regex(database, mongo_cache_repository, key, expected) -> None:
    database[CACHE_COLLECTION].insert_one(
        {"cache_key": key, "data": "data"},
    )
    assert mongo_cache_repository.has(r"^test(\sline-\d+)?$", regex=True) == expected


def test_delete_all(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_many(
        [
            {"cache_key": "test", "data": "data"},
            {"cache_key": "test line-42", "data": "data"},
            {"cache_key": "foobar", "data": "data"},
        ]
    )
    mongo_cache_repository.delete_all(pattern=r"^test(\sline-\d+)?$")
    assert database[CACHE_COLLECTION].find_one({"cache_key": "test"}) is None
    assert database[CACHE_COLLECTION].find_one({"cache_key": "test line-42"}) is None
    assert database[CACHE_COLLECTION].find_one({"cache_key": "foobar"}) is not None


def test_create_indexes(database, mongo_cache_repository) -> None:
    mongo_cache_repository.create_indexes()

    assert [("cache_key", 1)] in [
        index["key"]
        for index in database[CACHE_COLLECTION].index_information().values()
    ]

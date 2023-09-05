import pytest

CACHE_COLLECTION = "cache"


def test_set(database, mongo_cache_repository) -> None:
    mongo_cache_repository.set("test", {"data": "data"})

    inserted_text = database[CACHE_COLLECTION].find_one(
        {"_id": "test"}, projection={"_id": False, "_id": False}
    )
    assert inserted_text == {"data": "data"}


def test_has(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"_id": "test", "data": "data"})
    assert mongo_cache_repository.has("test") is True


def test_get(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"_id": "test", "data": "data"})
    assert mongo_cache_repository.get("test") == {"data": "data"}


def test_delete(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_one({"_id": "test", "data": "data"})
    mongo_cache_repository.delete("test")
    assert database[CACHE_COLLECTION].find_one({"_id": "test"}) is None


@pytest.mark.parametrize(
    "key,expected", [("test", True), ("test line-42", True), ("foobar", False)]
)
def test_exists_with_regex(database, mongo_cache_repository, key, expected) -> None:
    database[CACHE_COLLECTION].insert_one(
        {"_id": key, "data": "data"},
    )
    assert mongo_cache_repository.has(r"^test(\sline-\d+)?$", regex=True) == expected


def test_delete_all(database, mongo_cache_repository) -> None:
    database[CACHE_COLLECTION].insert_many(
        [
            {"_id": "test", "data": "data"},
            {"_id": "test line-42", "data": "data"},
            {"_id": "foobar", "data": "data"},
        ]
    )
    mongo_cache_repository.delete_all(pattern=r"^test(\sline-\d+)?$")
    assert database[CACHE_COLLECTION].find_one({"_id": "test"}) is None
    assert database[CACHE_COLLECTION].find_one({"_id": "test line-42"}) is None
    assert database[CACHE_COLLECTION].find_one({"_id": "foobar"}) is not None

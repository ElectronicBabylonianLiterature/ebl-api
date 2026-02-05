import pytest

CACHE_COLLECTION = "cache"


def test_set(database, mongo_cache_repository) -> None:
    mongo_cache_repository.set("test", {"data": "data"})

    inserted_text = database[CACHE_COLLECTION].find_one(
        {"cache_key": "test"}, projection={"_id": False, "cache_key": False}
    )
    assert inserted_text == {"data": "data"}


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

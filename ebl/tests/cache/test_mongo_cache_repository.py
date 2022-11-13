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

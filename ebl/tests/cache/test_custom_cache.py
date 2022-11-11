from ebl.cache.application.custom_cache import CustomCache


def test_custom_cache(mongo_cache_repository):
    custom_cache = CustomCache(mongo_cache_repository)
    assert custom_cache.has("test-key") is False

    custom_cache.set("test-key", {"item": "test-item"})
    assert custom_cache.has("test-key") is True
    assert custom_cache.get("test-key") == {"item": "test-item"}

from mockito import verify

from ebl.cache.application.custom_cache import CustomCache


def test_custom_cache_has(mongo_cache_repository, when):
    custom_cache = CustomCache(mongo_cache_repository)
    when(mongo_cache_repository).has("test-key").thenReturn(True)
    assert custom_cache.has("test-key") is True


def test_custom_cache_get(mongo_cache_repository, when):
    custom_cache = CustomCache(mongo_cache_repository)
    when(mongo_cache_repository).get("test-key").thenReturn({"item": "test-item"})
    assert custom_cache.get("test-key") == {"item": "test-item"}


def test_custom_cache_set(mongo_cache_repository, when):
    custom_cache = CustomCache(mongo_cache_repository)
    when(mongo_cache_repository).set("test-key", {"item": "test-item"}).thenReturn(None)
    custom_cache.set("test-key", {"item": "test-item"})
    verify(mongo_cache_repository, 1).set("test-key", {"item": "test-item"})


def test_custom_cache_delete(mongo_cache_repository, when):
    custom_cache = CustomCache(mongo_cache_repository)
    when(mongo_cache_repository).delete("test-key").thenReturn(None)
    custom_cache.delete("test-key")
    verify(mongo_cache_repository, 1).delete("test-key")

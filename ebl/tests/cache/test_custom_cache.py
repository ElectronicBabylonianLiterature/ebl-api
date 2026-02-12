from mockito import verify

from ebl.cache.application.custom_cache import ChapterCache
from ebl.tests.factories.corpus import ChapterFactory
from ebl.corpus.domain.chapter import ChapterId


def test_custom_cache_has(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    when(mongo_cache_repository).has("test-key").thenReturn(True)
    assert custom_cache.has("test-key") is True


def test_custom_cache_get(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    when(mongo_cache_repository).get("test-key").thenReturn({"item": "test-item"})
    assert custom_cache.get("test-key") == {"item": "test-item"}


def test_custom_cache_set(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    when(mongo_cache_repository).set("test-key", {"item": "test-item"}).thenReturn(None)
    custom_cache.set("test-key", {"item": "test-item"})
    verify(mongo_cache_repository, 1).set("test-key", {"item": "test-item"})


def test_custom_cache_delete(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    when(mongo_cache_repository).delete("test-key").thenReturn(None)
    custom_cache.delete("test-key")
    verify(mongo_cache_repository, 1).delete("test-key")


def test_custom_cache_delete_all(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    when(mongo_cache_repository).delete_all("^test-").thenReturn(None)
    custom_cache.delete_all(pattern="^test-")
    verify(mongo_cache_repository, 1).delete_all("^test-")


def test_custom_cache_delete_chapter(mongo_cache_repository, when):
    custom_cache = ChapterCache(mongo_cache_repository)
    chapter = ChapterFactory.build()
    chapter_id = ChapterId(chapter.text_id, chapter.stage, chapter.name)
    pattern = rf"^{str(chapter_id)}(\sline-\d+)?$"
    when(mongo_cache_repository).delete_all(pattern).thenReturn(None)
    custom_cache.delete_chapter(chapter_id)
    verify(mongo_cache_repository, 1).delete_all(pattern)

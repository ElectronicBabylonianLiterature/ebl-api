from typing import Iterator

import pytest
from pymongo.database import Database

from ebl.cache.application.custom_cache import CHAPTER_CACHE_KEY_PREFIX, ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.tests.factories.corpus import ChapterFactory


@pytest.fixture
def chapter_id() -> ChapterId:
    return ChapterFactory.build().id_


@pytest.fixture
def cache(mongo_cache_repository: MongoCacheRepository) -> ChapterCache:
    return ChapterCache(mongo_cache_repository)


def test_read_through_cache_reuses_current_revision(
    cache: ChapterCache, chapter_id: ChapterId
) -> None:
    values: Iterator[dict] = iter([{"value": "first"}, {"value": "second"}])

    def create() -> dict:
        return next(values)

    assert cache.get_or_create(chapter_id, str(chapter_id), create) == {
        "value": "first"
    }
    assert cache.get_or_create(chapter_id, str(chapter_id), create) == {
        "value": "first"
    }
    assert next(values) == {"value": "second"}


def test_legacy_cache_payload_is_rebuilt(
    cache: ChapterCache, chapter_id: ChapterId
) -> None:
    cache.set(str(chapter_id), {"value": "legacy"})
    cache.set(f"{CHAPTER_CACHE_KEY_PREFIX}{chapter_id}", {"value": "malformed"})
    assert cache.get_or_create(
        chapter_id, str(chapter_id), lambda: {"value": "new"}
    ) == {"value": "new"}


def test_completed_old_read_cannot_restore_stale_cache(
    cache: ChapterCache, chapter_id: ChapterId, database: Database
) -> None:
    other_worker = ChapterCache(MongoCacheRepository(database))
    value = {"value": "old"}

    def delayed_read() -> dict:
        old_value = dict(value)
        with other_worker.updating_chapter(chapter_id):
            value["value"] = "new"
        return old_value

    assert cache.get_or_create(chapter_id, str(chapter_id), delayed_read) == {
        "value": "old"
    }
    assert cache.get_or_create(chapter_id, str(chapter_id), lambda: dict(value)) == {
        "value": "new"
    }
    assert database["cache"].count_documents({}) == 1


def test_legacy_reader_cannot_see_wrapped_display(
    cache: ChapterCache, chapter_id: ChapterId, database: Database
) -> None:
    value: dict = {"lines": []}
    assert cache.get_or_create(chapter_id, str(chapter_id), lambda: value) == value
    assert database["cache"].find_one({"cache_key": str(chapter_id)}) is None
    cache.set(str(chapter_id), {"lines": ["legacy"]})
    legacy = database["cache"].find_one({"cache_key": str(chapter_id)})
    assert legacy is not None
    assert legacy["lines"] == ["legacy"]
    assert cache.get_or_create(chapter_id, str(chapter_id), lambda: {}) == value


def test_malformed_current_revision_payload_is_rebuilt(
    cache: ChapterCache, chapter_id: ChapterId
) -> None:
    cache.set(
        f"{CHAPTER_CACHE_KEY_PREFIX}{chapter_id}",
        {"chapterCacheRevision": 0, "value": "invalid"},
    )
    assert cache.get_or_create(chapter_id, str(chapter_id), lambda: {"lines": []}) == {
        "lines": []
    }


def test_reads_during_concurrent_writes_bypass_cache(
    cache: ChapterCache, chapter_id: ChapterId, database: Database
) -> None:
    other_worker = ChapterCache(MongoCacheRepository(database))
    with cache.updating_chapter(chapter_id):
        with other_worker.updating_chapter(chapter_id):
            assert cache.get_or_create(
                chapter_id, str(chapter_id), lambda: {"value": "pending"}
            ) == {"value": "pending"}
        assert database["cache"].count_documents({}) == 0
        assert cache.get_or_create(
            chapter_id, str(chapter_id), lambda: {"value": "still pending"}
        ) == {"value": "still pending"}
    assert database["cache"].count_documents({}) == 0
    assert cache.get_or_create(
        chapter_id, str(chapter_id), lambda: {"value": "committed"}
    ) == {"value": "committed"}
    assert database["cache"].count_documents({}) == 1


def test_failed_mutation_finishes_generation(
    cache: ChapterCache, chapter_id: ChapterId, database: Database
) -> None:
    def reject() -> None:
        with cache.updating_chapter(chapter_id):
            raise ValueError("rejected")

    pytest.raises(ValueError, reject).match("rejected")
    assert database["chapter_cache_state"].find_one({"_id": str(chapter_id)}) == {
        "_id": str(chapter_id),
        "pending": 0,
        "revision": 2,
    }


def test_exact_chapter_invalidation_preserves_other_chapters(
    cache: ChapterCache, chapter_id: ChapterId, database: Database
) -> None:
    other_key = str(chapter_id).replace(chapter_id.name, chapter_id.name + " extra")
    for key in (
        str(chapter_id),
        f"{chapter_id} line-0",
        f"{CHAPTER_CACHE_KEY_PREFIX}{chapter_id}",
        f"{CHAPTER_CACHE_KEY_PREFIX}{chapter_id} line-0",
        other_key,
        f"{CHAPTER_CACHE_KEY_PREFIX}{other_key}",
    ):
        cache.set(key, {"value": "existing"})
    with cache.updating_chapter(chapter_id):
        assert database["cache"].count_documents({}) == 2
    assert cache.get(other_key) == {"value": "existing"}
    assert cache.get(f"{CHAPTER_CACHE_KEY_PREFIX}{other_key}") == {"value": "existing"}

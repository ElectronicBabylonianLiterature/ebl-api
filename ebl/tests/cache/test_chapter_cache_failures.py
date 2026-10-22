import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pytest
from pymongo import ReadPreference
from pymongo.database import Database
from pymongo.errors import AutoReconnect, DuplicateKeyError
from pymongo.read_preferences import Nearest, Secondary

from ebl.cache.application.custom_cache import ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.tests.factories.corpus import ChapterFactory


def test_finish_failure_keeps_cache_bypassed(
    mongo_cache_repository: MongoCacheRepository,
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cache = ChapterCache(mongo_cache_repository)
    chapter_id = ChapterFactory.build().id_
    state = mongo_cache_repository._chapter_state
    with cache.updating_chapter(chapter_id):
        cache.get_or_create(chapter_id, str(chapter_id), lambda: {"value": "old"})

        def fail_finish(*args: object, **kwargs: object) -> None:
            raise AutoReconnect("lost cache connection")

        monkeypatch.setattr(state._collection, "update_one", fail_finish)
    assert "Chapter cache remains bypassed" in caplog.text
    assert database["cache"].count_documents({}) == 0
    assert cache.get_or_create(
        chapter_id, str(chapter_id), lambda: {"value": "new"}
    ) == {"value": "new"}
    assert database["cache"].count_documents({}) == 0


def test_state_read_failure_bypasses_existing_cache(
    mongo_cache_repository: MongoCacheRepository,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cache = ChapterCache(mongo_cache_repository)
    chapter_id: ChapterId = ChapterFactory.build().id_
    cache.get_or_create(chapter_id, str(chapter_id), lambda: {"value": "old"})

    def fail_read(*args: object, **kwargs: object) -> None:
        raise AutoReconnect("state unavailable")

    monkeypatch.setattr(
        mongo_cache_repository._chapter_state._collection, "find_one", fail_read
    )
    with caplog.at_level(logging.WARNING):
        result = cache.get_or_create(
            chapter_id, str(chapter_id), lambda: {"value": "new"}
        )
    assert result == {"value": "new"}
    assert "Bypassing chapter cache" in caplog.text


def test_repeated_cache_writes_replace_one_document(
    mongo_cache_repository: MongoCacheRepository, database: Database
) -> None:
    mongo_cache_repository.set("chapter", {"value": "old"})
    mongo_cache_repository.set("chapter", {"value": "new"})
    assert database["cache"].count_documents({"cache_key": "chapter"}) == 1
    assert mongo_cache_repository.get("chapter") == {"value": "new"}


def test_concurrent_upsert_survives_invalidation_before_retry(
    mongo_cache_repository: MongoCacheRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = mongo_cache_repository
    replace: Callable = repository._collection.replace_one
    calls = []

    def race(document: object, upsert: bool = False) -> object:
        calls.append(upsert)
        if len(calls) == 1:
            replace(document, upsert=True)
            repository._collection.delete_one({"cache_key": "chapter"})
            raise DuplicateKeyError("simultaneous cache insert")
        return replace(document, upsert=upsert)

    monkeypatch.setattr(repository._collection, "replace_one", race)
    repository.set("chapter", {"value": "current"})
    assert calls == [True, True]
    assert repository.get("chapter") == {"value": "current"}


def test_removing_missing_cache_entries_is_idempotent(
    mongo_cache_repository: MongoCacheRepository,
) -> None:
    mongo_cache_repository.delete("already gone")
    mongo_cache_repository.delete_all("already gone")
    assert not mongo_cache_repository.has("already gone")


def test_concurrent_workers_share_atomic_pending_state(database: Database) -> None:
    workers = [MongoCacheRepository(database) for _ in range(8)]
    chapter_key = str(ChapterFactory.build().id_)

    def start(worker: MongoCacheRepository) -> None:
        worker.start_chapter_update(chapter_key)

    def finish(worker: MongoCacheRepository) -> None:
        worker.finish_chapter_update(chapter_key)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(start, workers))
        assert workers[0].chapter_revision(chapter_key) is None
        list(executor.map(finish, workers))
    assert workers[0].chapter_revision(chapter_key) == 16
    assert database["chapter_cache_state"].find_one({"_id": chapter_key}) == {
        "_id": chapter_key,
        "pending": 0,
        "revision": 16,
    }


@pytest.mark.parametrize(
    "preference", [ReadPreference.SECONDARY, ReadPreference.NEAREST]
)
def test_non_primary_reads_bypass_cache_and_keep_mutation_generations(
    database: Database, preference: Secondary | Nearest
) -> None:
    primary_repository = MongoCacheRepository(database)
    primary_cache = ChapterCache(primary_repository)
    chapter_id = ChapterFactory.build().id_
    chapter_key = str(chapter_id)
    primary_cache.get_or_create(chapter_id, chapter_key, lambda: {"value": "old"})
    reader = MongoCacheRepository(database.with_options(read_preference=preference))
    cache = ChapterCache(reader)
    assert cache.get_or_create(chapter_id, chapter_key, lambda: {"value": "new"}) == {
        "value": "new"
    }
    assert primary_cache.get_or_create(chapter_id, chapter_key, lambda: {}) == {
        "value": "old"
    }
    with cache.updating_chapter(chapter_id):
        assert primary_repository.chapter_revision(chapter_key) is None
    assert primary_repository.chapter_revision(chapter_key) == 2
    assert reader.chapter_revision(chapter_key) is None
    for value in ("after mutation", "after another read"):

        def create(value: str = value) -> dict:
            return {"value": value}

        assert cache.get_or_create(chapter_id, chapter_key, create) == {"value": value}
        assert database["cache"].count_documents({}) == 0

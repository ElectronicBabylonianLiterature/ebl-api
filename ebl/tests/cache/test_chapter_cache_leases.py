from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import attr
import pytest
from pymongo.database import Database
from pymongo.errors import AutoReconnect

from ebl.cache.application.custom_cache import ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.cache.infrastructure.mongo_chapter_cache_state import MongoChapterCacheState
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.factories.corpus import ChapterFactory


def expire_writer(database: Database, chapter_key: str) -> None:
    database["chapter_cache_state"].update_one(
        {"_id": chapter_key},
        {"$set": {"pendingUntil": datetime.now(timezone.utc) - timedelta(minutes=1)}},
    )


def test_abandoned_writer_lease_recovers_without_counter_repair(
    database: Database,
) -> None:
    state = MongoChapterCacheState(database)
    before = state.revision("chapter")
    epoch = state.start_update("chapter")
    assert state.revision("chapter") is None
    expire_writer(database, "chapter")
    recovered = state.revision("chapter")
    assert recovered is not None
    assert recovered != before
    epoch = state.start_update("chapter")
    assert state.revision("chapter") is not None
    state.finish_update("chapter", epoch)
    assert state.revision("chapter") is not None


def test_completed_writers_cannot_extend_an_abandoned_lease(database: Database) -> None:
    state = MongoChapterCacheState(database)
    epoch = state.start_update("chapter")
    abandoned = database["chapter_cache_state"].find_one({"_id": "chapter"})
    assert abandoned is not None
    for _ in range(3):
        epoch = state.start_update("chapter")
        state.finish_update("chapter", epoch)
        stored = database["chapter_cache_state"].find_one({"_id": "chapter"})
        assert stored is not None
        assert stored["pendingUntil"] == abandoned["pendingUntil"]
        assert state.revision("chapter") is None
    expire_writer(database, "chapter")
    assert state.revision("chapter") is not None
    for _ in range(3):
        epoch = state.start_update("chapter")
        state.finish_update("chapter", epoch)
        assert state.revision("chapter") is not None


def test_late_finish_advances_revision_after_lease_expiry(database: Database) -> None:
    state = MongoChapterCacheState(database)
    epoch = state.start_update("chapter")
    expire_writer(database, "chapter")
    expired = state.revision("chapter")
    state.finish_update("chapter", epoch)
    assert state.revision("chapter") != expired
    assert str(state.revision("chapter")).endswith(":2")


def test_ambiguous_start_failure_recovers_after_expiry(database: Database) -> None:
    state = MongoChapterCacheState(database)
    original = state._collection.find_one_and_update

    def uncertain_start(filter_: dict, update: list[dict], **options: object) -> None:
        original(filter_, update, upsert=True)
        raise AutoReconnect("marker acknowledgement lost")

    with patch.object(state._collection, "find_one_and_update", uncertain_start):
        with pytest.raises(AutoReconnect):
            state.start_update("chapter")
    assert state.revision("chapter") is None
    expire_writer(database, "chapter")
    assert state.revision("chapter") is not None


def test_delayed_writer_commit_fences_cache_even_when_finish_fails(
    database: Database, text_repository: MongoTextRepository
) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    chapter = ChapterFactory.build(parser_version="old")
    text_repository.create_chapter(chapter)
    key = str(chapter.id_)

    def read() -> dict:
        return {
            "parserVersion": text_repository.find_chapter(chapter.id_).parser_version
        }

    epoch = state.start_update(key)
    expire_writer(database, key)
    assert cache.get_or_create(chapter.id_, key, read) == {"parserVersion": "old"}
    text_repository.update(chapter.id_, attr.evolve(chapter, parser_version="new"))
    with patch.object(state._collection, "update_one", side_effect=AutoReconnect):
        state.finish_update(key, epoch)
    assert cache.get_or_create(chapter.id_, key, read) == {"parserVersion": "new"}

    def unexpected_read() -> dict:
        pytest.fail("warm cache")

    assert cache.get_or_create(chapter.id_, key, unexpected_read) == {
        "parserVersion": "new"
    }


def test_expired_writer_during_cache_fill_cannot_repopulate_stale_content(
    database: Database, text_repository: MongoTextRepository
) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    chapter = ChapterFactory.build(parser_version="old")
    text_repository.create_chapter(chapter)
    key = str(chapter.id_)
    state.start_update(key)
    expire_writer(database, key)

    def delayed_read() -> dict:
        text_repository.update(chapter.id_, attr.evolve(chapter, parser_version="new"))
        return {"parserVersion": "old"}

    assert cache.get_or_create(chapter.id_, key, delayed_read) == {
        "parserVersion": "old"
    }
    assert cache.get_or_create(chapter.id_, key, lambda: {"parserVersion": "new"}) == {
        "parserVersion": "new"
    }


def test_content_revision_failure_bypasses_without_writing(database: Database) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    chapter_id = ChapterFactory.build().id_
    with patch.object(state._chapters, "find_one", side_effect=AutoReconnect):
        assert cache.get_or_create(
            chapter_id, str(chapter_id), lambda: {"new": True}
        ) == {"new": True}
    assert database["cache"].count_documents({}) == 0

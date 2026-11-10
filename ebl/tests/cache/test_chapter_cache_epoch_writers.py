from contextlib import ExitStack

import pytest
from pymongo.database import Database
from pymongo.errors import PyMongoError
from unittest.mock import patch

from ebl.cache.application.custom_cache import ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.cache.infrastructure.mongo_chapter_cache_state import MongoChapterCacheState
from ebl.tests.factories.corpus import ChapterFactory


def test_old_writer_finish_cannot_underflow_recreated_state(database: Database) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    chapter_id = ChapterFactory.build().id_
    key = str(chapter_id)

    with cache.updating_chapter(chapter_id):
        database["chapter_cache_state"].drop()
        assert cache.get_or_create(chapter_id, key, lambda: {"fresh": True}) == {
            "fresh": True
        }

    stored = database["chapter_cache_state"].find_one({"_id": key})
    assert stored is not None
    assert stored["pending"] == 0
    assert state.revision(key) is not None

    def unexpected_read() -> dict:
        pytest.fail("recreated state must leave the fresh cache usable")

    assert cache.get_or_create(chapter_id, key, unexpected_read) == {"fresh": True}


def test_old_writer_finish_preserves_new_epoch_active_writer(
    database: Database,
) -> None:
    state = MongoChapterCacheState(database)
    old_cache = ChapterCache(MongoCacheRepository(database), state)
    new_cache = ChapterCache(
        MongoCacheRepository(database), MongoChapterCacheState(database)
    )
    chapter_id = ChapterFactory.build().id_
    key = str(chapter_id)

    with ExitStack() as new_writer:
        with old_cache.updating_chapter(chapter_id):
            database["chapter_cache_state"].drop()
            new_writer.enter_context(new_cache.updating_chapter(chapter_id))
        assert state.revision(key) is None
        stored = database["chapter_cache_state"].find_one({"_id": key})
        assert stored is not None
        assert stored["pending"] == 1
        assert new_cache.get_or_create(chapter_id, key, lambda: {"live": True}) == {
            "live": True
        }
        assert database["cache"].count_documents({}) == 0

    assert state.revision(key) is not None


def test_unacknowledged_marker_never_starts_content_mutation(
    database: Database,
) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    chapter_id = ChapterFactory.build().id_

    with patch.object(state._collection, "find_one_and_update", return_value=None):
        with pytest.raises(PyMongoError, match="writer marker was not acknowledged"):
            with cache.updating_chapter(chapter_id):
                pytest.fail("unacknowledged marker must prevent content mutation")


def test_repeated_finish_cannot_make_pending_negative(database: Database) -> None:
    state = MongoChapterCacheState(database)
    epoch = state.start_update("chapter")
    state.finish_update("chapter", epoch)
    finished_revision = state.revision("chapter")
    state.finish_update("chapter", epoch)

    assert state.revision("chapter") == finished_revision
    stored = database["chapter_cache_state"].find_one({"_id": "chapter"})
    assert stored is not None
    assert stored["pending"] == 0

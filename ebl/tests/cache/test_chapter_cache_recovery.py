import json
import runpy
import sys
from typing import Sequence, cast
from unittest.mock import patch

import pytest
from pymongo import MongoClient, ReadPreference
from pymongo.database import Database
from pymongo.errors import AutoReconnect

from ebl.cache import clear_versioned_chapter_cache as cleanup
from ebl.cache.application.custom_cache import CHAPTER_CACHE_KEY_PREFIX, ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.cache.infrastructure.mongo_chapter_cache_state import MongoChapterCacheState
from ebl.errors import NotFoundError
from ebl.tests.factories.corpus import ChapterFactory


def test_lost_state_rotates_epoch_and_rejects_stale_wrappers(
    database: Database,
) -> None:
    cache = ChapterCache(
        MongoCacheRepository(database), MongoChapterCacheState(database)
    )
    chapter_id = ChapterFactory.build().id_
    key = str(chapter_id)
    cache.get_or_create(chapter_id, key, lambda: {"value": "old"})
    old_revision = cache._chapter_state.revision(key)
    database["chapter_cache_state"].drop()
    assert cache.get_or_create(chapter_id, key, lambda: {"value": "new"}) == {
        "value": "new"
    }
    assert cache._chapter_state.revision(key) != old_revision
    assert cache.get_or_create(chapter_id, key, lambda: {}) == {"value": "new"}


def test_existing_state_gets_epoch_without_losing_pending_writers(
    database: Database,
) -> None:
    state = MongoChapterCacheState(database)
    database["chapter_cache_state"].insert_one(
        {"_id": "chapter", "pending": 1, "revision": 7}
    )
    assert state.revision("chapter") is None
    state.finish_update("chapter")
    assert str(state.revision("chapter")).endswith(":8")
    stored = database["chapter_cache_state"].find_one({"_id": "chapter"})
    assert stored is not None
    assert stored["pending"] == 0


def test_missing_state_after_initialization_bypasses_cache(database: Database) -> None:
    state = MongoChapterCacheState(database)
    with patch.object(state._collection, "find_one", return_value=None):
        assert state.revision("chapter") is None


def test_pending_warning_is_bounded_and_repeatable(
    database: Database, caplog: pytest.LogCaptureFixture
) -> None:
    state = MongoChapterCacheState(database)
    state.start_update("chapter")
    with patch(
        "ebl.cache.infrastructure.mongo_chapter_cache_state.monotonic",
        side_effect=[0, 30, 60],
    ):
        assert state.revision("chapter") is None
        assert state.revision("chapter") is None
        assert state.revision("chapter") is None
    assert caplog.text.count("has pending writers") == 2


def test_non_primary_state_warns_at_construction(
    database: Database, caplog: pytest.LogCaptureFixture
) -> None:
    state = MongoChapterCacheState(
        database.with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
    )
    assert state.revision("chapter") is None
    assert state.revision("chapter") is None
    assert caplog.text.count("read preference is not primary") == 1


def test_ambiguous_start_failure_keeps_pending_and_never_starts_mutation(
    database: Database,
) -> None:
    state = MongoChapterCacheState(database)
    cache = ChapterCache(MongoCacheRepository(database), state)
    original_update = state._collection.update_one
    chapter_id = ChapterFactory.build().id_

    def uncertain_update(filter_: dict, update: dict, upsert: bool = False) -> None:
        original_update(filter_, update, upsert=upsert)
        raise AutoReconnect("result lost after server accepted write")

    with patch.object(state._collection, "update_one", uncertain_update):
        with pytest.raises(AutoReconnect):
            with cache.updating_chapter(chapter_id):
                pytest.fail("mutation must not start after an ambiguous marker failure")
    assert state.revision(str(chapter_id)) is None


@pytest.mark.parametrize("repair_pending", [False, True])
def test_quiescent_cleanup_preserves_unrelated_entries_and_recovers_only_on_request(
    database: Database, repair_pending: bool
) -> None:
    state = MongoChapterCacheState(database)
    repository = MongoCacheRepository(database)
    state.start_update("abandoned")
    state.start_update("finished")
    state.finish_update("finished")
    original_states = list(database["chapter_cache_state"].find({}).sort("_id"))
    repository.set(f"{CHAPTER_CACHE_KEY_PREFIX}abandoned", {"value": "stale"})
    repository.set("unrelated", {"value": "kept"})
    result = cleanup.clear_versioned_chapter_cache(database, repair_pending)
    assert result == {"clearedEntries": 1, "repairedChapters": int(repair_pending)}
    assert repository.get("unrelated") == {"value": "kept"}
    assert database["cache"].count_documents({}) == 1
    if repair_pending:
        assert str(state.revision("abandoned")).endswith(":2")
        assert (
            database["chapter_cache_state"].find_one({"_id": "finished"})
            == original_states[1]
        )
        recovered = database["chapter_cache_state"].find_one({"_id": "abandoned"})
        assert recovered is not None
        assert recovered["epoch"] != original_states[0]["epoch"]
    else:
        assert (
            list(database["chapter_cache_state"].find({}).sort("_id"))
            == original_states
        )
        assert state.revision("abandoned") is None
    assert (
        cleanup.clear_versioned_chapter_cache(database, repair_pending)[
            "clearedEntries"
        ]
        == 0
    )


@pytest.mark.parametrize("module_entrypoint", [False, True])
def test_cleanup_cli_uses_only_explicit_database_and_uri(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    module_entrypoint: bool,
) -> None:
    arguments: Sequence[str] = [
        "--uri-env",
        "CACHE_RECOVERY_TEST_URI",
        "--database",
        database.name,
        "--confirm-quiescent",
        "--repair-pending",
    ]
    monkeypatch.setenv("CACHE_RECOVERY_TEST_URI", "mongodb://explicit-test-endpoint")
    with (
        patch.object(MongoClient, "__enter__", return_value=database.client),
        patch.object(MongoClient, "__exit__"),
        patch("pymongo.MongoClient", return_value=database.client),
    ):
        if module_entrypoint:
            monkeypatch.setattr(sys, "argv", ["cleanup", *arguments])
            with pytest.raises(SystemExit) as exit_result:
                runpy.run_module(
                    "ebl.cache.clear_versioned_chapter_cache", run_name="__main__"
                )
            assert exit_result.value.code == 0
        else:
            with patch.object(
                cleanup, "MongoClient", return_value=database.client
            ) as constructor:
                assert cleanup.main(arguments) == 0
            constructor.assert_called_once_with(
                "mongodb://explicit-test-endpoint",
                read_preference=ReadPreference.PRIMARY,
            )
    output, _ = cast(tuple[str, str], capsys.readouterr())
    assert json.loads(output) == {
        "clearedEntries": 0,
        "repairedChapters": 0,
    }


def test_versioned_miss_does_not_fall_back_to_legacy_query(database: Database) -> None:
    repository = MongoCacheRepository(database)
    with patch.object(
        repository._collection, "find_one", side_effect=AssertionError("extra lookup")
    ):
        with pytest.raises(NotFoundError):
            repository.get(f"{CHAPTER_CACHE_KEY_PREFIX}missing")

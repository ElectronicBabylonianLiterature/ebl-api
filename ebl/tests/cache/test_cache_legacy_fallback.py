from unittest.mock import patch

import pytest
from pymongo.database import Database

from ebl.cache.application.custom_cache import CHAPTER_CACHE_KEY_PREFIX, ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.cache.infrastructure.mongo_chapter_cache_state import MongoChapterCacheState
from ebl.corpus.domain.chapter import ChapterId
from ebl.errors import NotFoundError
from ebl.tests.factories.corpus import ChapterFactory


@pytest.mark.parametrize("key", ["generic-key", f"{CHAPTER_CACHE_KEY_PREFIX}legacy"])
def test_legacy_fallback_is_selected_by_the_caller(
    database: Database, key: str
) -> None:
    database["cache"].insert_one({"cache_key": key, "value": "legacy"})
    repository = MongoCacheRepository(database)

    with pytest.raises(NotFoundError):
        repository.get(key, legacy_fallback=False)

    assert repository.get(key) == {"value": "legacy"}


def test_chapter_display_miss_skips_the_legacy_lookup(database: Database) -> None:
    repository = MongoCacheRepository(database)
    cache = ChapterCache(repository, MongoChapterCacheState(database))
    chapter = ChapterFactory.build()
    chapter_id = ChapterId(chapter.text_id, chapter.stage, chapter.name)

    with patch.object(
        repository._collection, "find_one", side_effect=AssertionError("legacy lookup")
    ):
        assert cache.get_or_create(
            chapter_id, str(chapter_id), lambda: {"lines": []}
        ) == {"lines": []}

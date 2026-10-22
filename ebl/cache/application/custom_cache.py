import attr
import re
from contextlib import contextmanager
from typing import Callable, Iterator, cast

from ebl.cache.application.cache_repository import CacheRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.errors import NotFoundError


CHAPTER_CACHE_KEY_PREFIX = "chapter-display-v2:"


@attr.attrs(auto_attribs=True, frozen=True)
class CustomCache:
    _mongo_cache_repository: CacheRepository

    def has(self, key: str) -> bool:
        return self._mongo_cache_repository.has(key)

    def get(self, key: str) -> dict:
        return self._mongo_cache_repository.get(key)

    def set(self, key: str, item: dict) -> None:
        self._mongo_cache_repository.set(key, item)

    def delete(self, key: str) -> None:
        self._mongo_cache_repository.delete(key)

    def delete_all(self, pattern: str) -> None:
        self._mongo_cache_repository.delete_all(pattern)


@attr.attrs(auto_attribs=True, frozen=True)
class ChapterCache(CustomCache):
    def delete_chapter(self, chapter_id: ChapterId) -> None:
        self.delete_all(
            pattern=rf"^({CHAPTER_CACHE_KEY_PREFIX})?{re.escape(str(chapter_id))}(\sline-\d+)?$"
        )

    @contextmanager
    def updating_chapter(self, chapter_id: ChapterId) -> Iterator[None]:
        chapter_key = str(chapter_id)
        self._mongo_cache_repository.start_chapter_update(chapter_key)
        try:
            self.delete_chapter(chapter_id)
            yield
        finally:
            self._mongo_cache_repository.finish_chapter_update(chapter_key)

    def get_or_create(
        self, chapter_id: ChapterId, key: str, create: Callable[[], dict]
    ) -> dict:
        revision = self._mongo_cache_repository.chapter_revision(str(chapter_id))
        if revision is None:
            return create()
        cache_key = f"{CHAPTER_CACHE_KEY_PREFIX}{key}"
        try:
            cached = self.get(cache_key)
        except NotFoundError:
            cached = {}
        if cached.get("chapterCacheRevision") == revision and isinstance(
            cached.get("value"), dict
        ):
            return cast(dict, cached["value"])
        value = create()
        self.set(cache_key, {"chapterCacheRevision": revision, "value": value})
        return value

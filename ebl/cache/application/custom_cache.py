import attr

from ebl.cache.application.cache_repository import CacheRepository
from ebl.corpus.domain.chapter import ChapterId


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
        self.delete_all(pattern=rf"^{str(chapter_id)}(\sline-\d+)?$")

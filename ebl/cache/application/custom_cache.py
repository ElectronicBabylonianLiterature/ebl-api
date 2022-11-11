import attr

from ebl.cache.application.cache_repository import CacheRepository


@attr.attrs(auto_attribs=True, frozen=True)
class CustomCache:
    _mongo_cache_repository: CacheRepository

    def has(self, key: str) -> bool:
        return self._mongo_cache_repository.has(key)

    def get(self, key: str) -> dict:
        return self._mongo_cache_repository.get(key)

    def set(self, key: str, item: any) -> None:
        self._mongo_cache_repository.set(key, item)

    def delete(self, key: str) -> None:
        self._mongo_cache_repository.delete(key)

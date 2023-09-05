from pymongo.database import Database

from ebl.cache.application.cache_repository import CacheRepository
from ebl.mongo_collection import MongoCollection


COLLECTION = "cache"


class MongoCacheRepository(CacheRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def has(self, cache_key: str, regex=False) -> bool:
        return self._collection.exists(
            {"_id": {"$regex": cache_key} if regex else cache_key}
        )

    def get(self, cache_key: str) -> dict:
        return self._collection.find_one({"_id": cache_key}, projection={"_id": 0})

    def set(self, cache_key: str, item: dict) -> None:
        self.delete(cache_key)
        self._collection.insert_one({"_id": cache_key, **item})

    def delete(self, cache_key: str) -> None:
        if self.has(cache_key):
            self._collection.delete_one({"_id": cache_key})

    def delete_all(self, pattern: str) -> None:
        if self.has(pattern, regex=True):
            self._collection.delete_many({"_id": {"$regex": pattern}})

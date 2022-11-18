from pymongo.database import Database

from ebl.cache.application.cache_repository import CacheRepository
from ebl.mongo_collection import MongoCollection

COLLECTION = "cache"


class MongoCacheRepository(CacheRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def has(self, cache_key: str) -> bool:
        return self._collection.exists({"cache_key": cache_key})

    def get(self, cache_key: str) -> dict:
        return self._collection.find_one(
            {"cache_key": cache_key}, projection={"cache_key": 0, "_id": 0}
        )

    def set(self, cache_key: str, item: dict) -> None:
        self._collection.insert_one({"cache_key": cache_key, **item})

    def delete(self, cache_key: str) -> None:
        if self.has(cache_key):
            self._collection.delete_one({"cache_key": cache_key})

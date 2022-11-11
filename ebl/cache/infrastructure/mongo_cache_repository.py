from pymongo.database import Database

from ebl.cache.application.cache_repository import CacheRepository
from ebl.mongo_collection import MongoCollection

COLLECTION = "cache"


class MongoCacheRepository(CacheRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def has(self, key: str) -> bool:
        return self._collection.exists({"key": key})

    def get(self, key: str) -> dict:
        return self._collection.find_one({"key": key}, projection={"key": 0, "_id": 0})

    def set(self, key: str, item: any) -> None:
        self._collection.insert_one({"key": key, **item})

    def delete(self, key: str) -> None:
        if self.has(key):
            self._collection.delete_one({"key": key})

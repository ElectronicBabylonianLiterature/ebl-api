import logging

import bson
import pymongo
from bson import ObjectId
from pymongo.common import MAX_BSON_SIZE
from pymongo.database import Database

from ebl.cache.application.cache_repository import CacheRepository
from ebl.mongo_collection import MongoCollection


COLLECTION = "cache"

logger = logging.getLogger(__name__)


class MongoCacheRepository(CacheRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        self._collection.create_index([("cache_key", pymongo.ASCENDING)])

    def has(self, cache_key: str, regex=False) -> bool:
        return self._collection.exists(
            {"cache_key": {"$regex": cache_key} if regex else cache_key}
        )

    def get(self, cache_key: str) -> dict:
        return self._collection.find_one(
            {"cache_key": cache_key}, projection={"cache_key": 0, "_id": 0}
        )

    def set(self, cache_key: str, item: dict) -> None:
        document = {"_id": ObjectId(), "cache_key": cache_key, **item}
        size = len(bson.encode(document))
        if size > MAX_BSON_SIZE:
            logger.warning(
                "Not caching %s: %d bytes exceeds %d", cache_key, size, MAX_BSON_SIZE
            )
        else:
            self._collection.insert_one(document)

    def delete(self, cache_key: str) -> None:
        if self.has(cache_key):
            self._collection.delete_one({"cache_key": cache_key})

    def delete_all(self, pattern: str) -> None:
        if self.has(pattern, regex=True):
            self._collection.delete_many({"cache_key": {"$regex": pattern}})

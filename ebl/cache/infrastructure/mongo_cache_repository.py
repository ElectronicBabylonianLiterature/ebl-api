import logging
import re

import bson
import pymongo
from bson.raw_bson import RawBSONDocument
from pymongo.common import MAX_BSON_SIZE
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from typing import Optional

from ebl.cache.application.cache_repository import CacheRepository
from ebl.cache.infrastructure.mongo_chapter_cache_state import MongoChapterCacheState
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection


COLLECTION = "cache"

logger = logging.getLogger(__name__)


class MongoCacheRepository(CacheRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)
        self._chapter_state = MongoChapterCacheState(database)

    def create_indexes(self) -> None:
        self._collection.create_index([("cache_key", pymongo.ASCENDING)])

    def has(self, cache_key: str, regex=False) -> bool:
        return self._collection.exists(
            {"cache_key": {"$regex": cache_key} if regex else cache_key}
        )

    def get(self, cache_key: str) -> dict:
        documents = self._collection.find_many(
            {"_id": self._document_id(cache_key)}, projection={"cache_key": 0, "_id": 0}
        )
        document = next(documents, None)
        if document is not None:
            return document
        return self._collection.find_one(
            {"cache_key": cache_key}, projection={"cache_key": 0, "_id": 0}
        )

    def set(self, cache_key: str, item: dict) -> None:
        encoded_document = bson.encode(
            {**item, "_id": self._document_id(cache_key), "cache_key": cache_key}
        )
        size = len(encoded_document)
        if size > MAX_BSON_SIZE:
            logger.warning(
                "Not caching %s: %d bytes exceeds %d", cache_key, size, MAX_BSON_SIZE
            )
        else:
            document = RawBSONDocument(encoded_document)
            for attempt in range(2):
                try:
                    self._collection.replace_one(document, upsert=True)
                    return
                except DuplicateKeyError:
                    if attempt == 1:
                        logger.warning(
                            "Not caching %s: repeated concurrent cache fills", cache_key
                        )

    def delete(self, cache_key: str) -> None:
        self.delete_all(rf"^{re.escape(cache_key)}$")

    def delete_all(self, pattern: str) -> None:
        try:
            self._collection.delete_many({"cache_key": {"$regex": pattern}})
        except NotFoundError:
            return

    def chapter_revision(self, chapter_key: str) -> Optional[int]:
        return self._chapter_state.revision(chapter_key)

    def start_chapter_update(self, chapter_key: str) -> None:
        self._chapter_state.start_update(chapter_key)

    def finish_chapter_update(self, chapter_key: str) -> None:
        self._chapter_state.finish_update(chapter_key)

    @staticmethod
    def _document_id(cache_key: str) -> str:
        return f"chapter-cache-v2:{cache_key}"

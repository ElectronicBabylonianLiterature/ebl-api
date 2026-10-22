import logging
from typing import Optional

from pymongo import ReadPreference
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError


COLLECTION = "chapter_cache_state"
logger = logging.getLogger(__name__)


class MongoChapterCacheState:
    def __init__(self, database: Database) -> None:
        self._collection: Collection = database[COLLECTION]

    def revision(self, chapter_key: str) -> Optional[int]:
        if self._collection.read_preference != ReadPreference.PRIMARY:
            return None
        try:
            state = self._collection.find_one({"_id": chapter_key})
        except PyMongoError:
            logger.warning("Bypassing chapter cache: cannot read %s state", chapter_key)
            return None
        if state is None:
            return 0
        return None if state["pending"] else int(state["revision"])

    def start_update(self, chapter_key: str) -> None:
        self._collection.update_one(
            {"_id": chapter_key}, {"$inc": {"pending": 1, "revision": 1}}, upsert=True
        )

    def finish_update(self, chapter_key: str) -> None:
        try:
            self._collection.update_one(
                {"_id": chapter_key}, {"$inc": {"pending": -1, "revision": 1}}
            )
        except PyMongoError:
            logger.warning(
                "Chapter cache remains bypassed: cannot finish %s update", chapter_key
            )

import logging
from time import monotonic
from typing import Optional

from bson import ObjectId
from pymongo import ReadPreference
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError


COLLECTION = "chapter_cache_state"
logger = logging.getLogger(__name__)
WARNING_INTERVAL_SECONDS = 60


class MongoChapterCacheState:
    def __init__(self, database: Database) -> None:
        self._collection: Collection = database[COLLECTION]
        self._warnings: dict[str, float] = {}
        if self._collection.read_preference != ReadPreference.PRIMARY:
            logger.warning("Bypassing chapter cache: read preference is not primary")

    def _warn(self, reason: str, message: str, chapter_key: str) -> None:
        now = monotonic()
        previous = self._warnings.get(reason)
        if previous is None or now - previous >= WARNING_INTERVAL_SECONDS:
            logger.warning(message, chapter_key)
            self._warnings[reason] = now

    def revision(self, chapter_key: str) -> Optional[str]:
        if self._collection.read_preference != ReadPreference.PRIMARY:
            return None
        try:
            state = self._collection.find_one({"_id": chapter_key})
            if state is None:
                self._collection.update_one(
                    {"_id": chapter_key},
                    {
                        "$setOnInsert": {
                            "epoch": str(ObjectId()),
                            "pending": 0,
                            "revision": 0,
                        }
                    },
                    upsert=True,
                )
                state = self._collection.find_one({"_id": chapter_key})
            if state is not None and "epoch" not in state:
                self._collection.update_one(
                    {"_id": chapter_key, "epoch": {"$exists": False}},
                    {"$set": {"epoch": str(ObjectId())}},
                )
                state = self._collection.find_one({"_id": chapter_key})
        except PyMongoError:
            self._warn(
                "read", "Bypassing chapter cache: cannot read %s state", chapter_key
            )
            return None
        if state is None:
            return None
        if state["pending"]:
            self._warn(
                "pending",
                "Bypassing chapter cache: %s has pending writers; "
                "use the quiescent chapter-cache recovery command if abandoned",
                chapter_key,
            )
            return None
        return f"{state['epoch']}:{int(state['revision'])}"

    def start_update(self, chapter_key: str) -> None:
        self._collection.update_one(
            {"_id": chapter_key},
            {
                "$inc": {"pending": 1, "revision": 1},
                "$setOnInsert": {"epoch": str(ObjectId())},
            },
            upsert=True,
        )

    def finish_update(self, chapter_key: str) -> None:
        try:
            self._collection.update_one(
                {"_id": chapter_key}, {"$inc": {"pending": -1, "revision": 1}}
            )
        except PyMongoError:
            self._warn(
                "finish",
                "Chapter cache remains bypassed: cannot finish %s update",
                chapter_key,
            )

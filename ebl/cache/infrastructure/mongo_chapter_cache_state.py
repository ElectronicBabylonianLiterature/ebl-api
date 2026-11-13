import logging
from time import monotonic
from typing import Optional

from bson import ObjectId
from pymongo import ReadPreference, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION


COLLECTION = "chapter_cache_state"
logger = logging.getLogger(__name__)
WARNING_INTERVAL_SECONDS = 60
PENDING_LEASE_MILLISECONDS = 5 * 60 * 1000


class MongoChapterCacheState:
    def __init__(self, database: Database) -> None:
        self._collection: Collection = database[COLLECTION]
        self._chapters: Collection = database[CHAPTERS_COLLECTION]
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
            state = self._read_state(chapter_key)
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
                state = self._read_state(chapter_key)
            if state is not None and "epoch" not in state:
                self._collection.update_one(
                    {"_id": chapter_key, "epoch": {"$exists": False}},
                    {"$set": {"epoch": str(ObjectId())}},
                )
                state = self._read_state(chapter_key)
        except PyMongoError:
            self._warn(
                "read", "Bypassing chapter cache: cannot read %s state", chapter_key
            )
            return None
        if state is None:
            return None
        if state["pending"] and not state.get("leaseExpired", False):
            self._warn(
                "pending",
                "Bypassing chapter cache: %s has pending writers; "
                "use the quiescent chapter-cache recovery command if abandoned",
                chapter_key,
            )
            return None
        return f"{state['epoch']}:{int(state['revision'])}"

    def _read_state(self, chapter_key: str) -> Optional[dict]:
        return self._collection.find_one(
            {"_id": chapter_key},
            projection={
                "epoch": 1,
                "pending": 1,
                "revision": 1,
                "leaseExpired": {
                    "$lte": [
                        {"$ifNull": ["$pendingUntil", {"$add": ["$$NOW", 1]}]},
                        "$$NOW",
                    ]
                },
            },
        )

    def content_revision(self, chapter_id: ChapterId) -> Optional[str]:
        try:
            chapter = self._chapters.find_one(
                chapter_id_query(chapter_id), projection={"_cacheRevision": 1}
            )
        except PyMongoError:
            self._warn(
                "content",
                "Bypassing chapter cache: cannot read %s content revision",
                str(chapter_id),
            )
            return None
        return (
            f"{chapter['_id']}:{chapter.get('_cacheRevision', 'legacy')}"
            if chapter is not None
            else "missing"
        )

    def start_update(self, chapter_key: str) -> str:
        state = self._collection.find_one_and_update(
            {"_id": chapter_key},
            [
                {
                    "$set": {
                        "pending": {"$add": [{"$ifNull": ["$pending", 0]}, 1]},
                        "revision": {"$add": [{"$ifNull": ["$revision", 0]}, 1]},
                        "epoch": {"$ifNull": ["$epoch", str(ObjectId())]},
                        "pendingUntil": {
                            "$cond": [
                                {"$gt": [{"$ifNull": ["$pending", 0]}, 0]},
                                {
                                    "$ifNull": [
                                        "$pendingUntil",
                                        {"$add": ["$$NOW", PENDING_LEASE_MILLISECONDS]},
                                    ]
                                },
                                {"$add": ["$$NOW", PENDING_LEASE_MILLISECONDS]},
                            ]
                        },
                    }
                }
            ],
            upsert=True,
            return_document=ReturnDocument.AFTER,
            projection={"epoch": 1},
        )
        if state is None:
            raise PyMongoError("Chapter cache writer marker was not acknowledged.")
        return str(state["epoch"])

    def finish_update(self, chapter_key: str, epoch: str) -> None:
        try:
            self._collection.update_one(
                {"_id": chapter_key, "epoch": epoch, "pending": {"$gt": 0}},
                {"$inc": {"pending": -1, "revision": 1}},
            )
        except PyMongoError:
            self._warn(
                "finish",
                "Cannot finish %s chapter cache state update; content revision remains fenced",
                chapter_key,
            )

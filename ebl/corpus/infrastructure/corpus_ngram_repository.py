from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    CHAPTER_NGRAM_COLLECTION,
    CHAPTERS_COLLECTION,
)
from typing import Optional, Sequence

from ebl.common.query.util import aggregate_all_ngrams, replace_all

NGRAM_FIELD = "ngram"


class ChapterNGramRepository:
    def __init__(self, database):
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)
        self._ngrams = MongoCollection(database, CHAPTER_NGRAM_COLLECTION)

    def aggregate_chapter_ngrams(
        self,
        chapter_id: ChapterId,
        N: Sequence[int],
        signs_to_exclude: Optional[Sequence[str]] = None,
    ):
        return [
            {"$match": chapter_id_query(chapter_id)},
            {"$project": {"signs": 1}},
            {"$unwind": "$signs"},
            {
                "$project": {
                    NGRAM_FIELD: {
                        "$split": [
                            replace_all("#", " # "),
                            " ",
                        ]
                    }
                }
            },
            *aggregate_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD, signs_to_exclude),
            {"$unwind": f"${NGRAM_FIELD}"},
            {
                "$group": {
                    "_id": None,
                    f"{NGRAM_FIELD}s": {"$addToSet": f"${NGRAM_FIELD}"},
                }
            },
            {"$project": {"_id": False}},
        ]

    def update_ngrams(
        self,
        chapter_id: ChapterId,
        N: Sequence[int],
        signs_to_exclude: Optional[Sequence[str]] = None,
    ) -> None:
        aggregation = self.aggregate_chapter_ngrams(chapter_id, N, signs_to_exclude)
        if data := next(
            self._chapters.aggregate(aggregation, allowDiskUse=True),
            None,
        ):
            try:
                self._ngrams.update_one(
                    {"_id": data["_id"]}, {"$set": {"ngrams": data["ngrams"]}}
                )
            except NotFoundError:
                self._ngrams.insert_one(data)

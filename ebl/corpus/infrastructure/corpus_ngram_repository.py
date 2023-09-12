from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    CHAPTER_NGRAM_COLLECTION,
    CHAPTERS_COLLECTION,
)
from typing import Sequence

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
    ):
        return [
            {"$match": chapter_id_query(chapter_id)},
            {"$project": {"signs": 1, "textId": 1, "stage": 1, "name": 1}},
            {"$unwind": "$signs"},
            {
                "$addFields": {
                    NGRAM_FIELD: {
                        "$split": [
                            replace_all("\n", " # "),
                            " ",
                        ]
                    }
                }
            },
            *aggregate_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD),
            {"$unwind": f"${NGRAM_FIELD}"},
            {
                "$group": {
                    "_id": None,
                    NGRAM_FIELD: {"$addToSet": f"${NGRAM_FIELD}"},
                    "textId": {"$first": "$textId"},
                    "name": {"$first": "$name"},
                    "stage": {"$first": "$stage"},
                }
            },
            {"$project": {"_id": False}},
        ]

    def update_ngrams(
        self,
        chapter_id: ChapterId,
        N: Sequence[int],
    ) -> None:
        aggregation = self.aggregate_chapter_ngrams(chapter_id, N)
        if data := next(
            self._chapters.aggregate(aggregation, allowDiskUse=True),
            None,
        ):
            try:
                self._ngrams.update_one(
                    chapter_id_query(chapter_id),
                    {"$set": {NGRAM_FIELD: data[NGRAM_FIELD]}},
                )
            except NotFoundError:
                self._ngrams.insert_one(data)

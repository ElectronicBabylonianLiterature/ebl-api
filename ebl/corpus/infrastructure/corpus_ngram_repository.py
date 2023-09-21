from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    CHAPTER_NGRAM_COLLECTION,
    CHAPTERS_COLLECTION,
)
from typing import List, Optional, Sequence, Set, Tuple

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
    ) -> Sequence[dict]:
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

    def set_ngrams(
        self,
        chapter_id: ChapterId,
        N: Sequence[int],
    ) -> Set[Tuple[str]]:
        aggregation = self.aggregate_chapter_ngrams(chapter_id, N)
        data = next(
            self._chapters.aggregate(aggregation, allowDiskUse=True),
            {NGRAM_FIELD: [], **ChapterIdSchema().dump(chapter_id)},
        )
        try:
            self._ngrams.update_one(
                chapter_id_query(chapter_id),
                {"$set": {NGRAM_FIELD: data[NGRAM_FIELD]}},
            )
        except NotFoundError:
            self._ngrams.insert_one(data)

        return {tuple(ngram) for ngram in data[NGRAM_FIELD]}

    def get_ngrams(self, chapter_id: ChapterId) -> Set[Tuple[str]]:
        ngrams = self._ngrams.find_one(chapter_id_query(chapter_id))[NGRAM_FIELD]

        return {tuple(ngram) for ngram in ngrams}

    def get_or_set_ngrams(
        self, chapter_id: ChapterId, N: Sequence[int]
    ) -> Set[Tuple[str]]:
        try:
            return self.get_ngrams(chapter_id)
        except NotFoundError:
            ngrams = self.set_ngrams(chapter_id, N)

        return ngrams

    def compute_overlaps(
        self, ngrams: Set[Tuple[str]], limit: Optional[int] = None
    ) -> Sequence[dict]:
        ngram_list = list(ngrams)
        pipeline: List[dict] = [
            {"$match": {"textId.category": {"$ne": 99}}},
            {
                "$project": {
                    "_id": 0,
                    "textId": 1,
                    "name": 1,
                    "stage": 1,
                    "overlap": {
                        "$let": {
                            "vars": {
                                "intersection": {
                                    "$size": {
                                        "$setIntersection": ["$ngram", ngram_list]
                                    }
                                },
                                "minLength": {
                                    "$min": [
                                        {"$size": "$ngram"},
                                        {"$size": [ngram_list]},
                                    ]
                                },
                            },
                            "in": {
                                "$cond": [
                                    {"$eq": ["$$minLength", 0]},
                                    0.0,
                                    {"$divide": ["$$intersection", "$$minLength"]},
                                ]
                            },
                        }
                    },
                }
            },
            {"$sort": {"overlap": -1}},
        ]

        if limit:
            pipeline.append({"$limit": limit})

        return list(self._ngrams.aggregate(pipeline, allowDiskUse=True))

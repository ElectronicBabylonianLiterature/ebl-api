import re
from typing import Sequence

from ebl.changelog import Changelog
from ebl.dictionary.application.word_repository import WordRepository
from ebl.dictionary.domain.word import WordId
from ebl.mongo_collection import MongoCollection

COLLECTION = "words"
LEMMA_SEARCH_LIMIT = 15


def _create_substring_expression(query, _input):
    return {
        "$eq": [
            {
                "$substrCP": [
                    {
                        "$reduce": {
                            "input": _input,
                            "initialValue": "",
                            "in": {"$concat": ["$$value", "$$this", " "]},
                        }
                    },
                    0,
                    len(query),
                ]
            },
            query,
        ]
    }


def _create_lemma_search_pipeline(query):
    return [
        {
            "$match": {
                "$or": [
                    {"$expr": _create_substring_expression(query, "$lemma")},
                    {
                        "$expr": {
                            "$anyElementTrue": {
                                "$map": {
                                    "input": "$forms",
                                    "as": "form",
                                    "in": _create_substring_expression(
                                        query, "$$form.lemma"
                                    ),
                                }
                            }
                        }
                    },
                ]
            }
        },
        {
            "$addFields": {
                "lemmaLength": {
                    "$sum": {
                        "$map": {
                            "input": "$lemma",
                            "as": "part",
                            "in": {"$strLenCP": "$$part"},
                        }
                    }
                }
            }
        },
        {"$sort": {"lemmaLength": 1, "_id": 1}},
        {"$limit": LEMMA_SEARCH_LIMIT},
        {"$project": {"lemmaLength": 0}},
    ]


class MongoWordRepository(WordRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)
        self._changelog = Changelog(database)

    def create(self, document):
        return self._collection.insert_one(document)

    def query_by_id(self, id_: WordId):
        return self._collection.find_one_by_id(id_)

    def query_by_ids(self, ids: Sequence[str]) -> Sequence:
        cursor = self._collection.aggregate(
            [
                {
                    "$match": {"_id": {"$in": ids}},
                }
            ]
        )
        return list(cursor)

    def query_by_lemma_meaning_root_vowels(
        self,
        word: str = "",
        meaning: str = "",
        root: str = "",
        vowelClass: str = "",
    ) -> Sequence:
        _lemma = {"$or": [{"lemma": word}, {"forms.lemma": word}]} if word else {}
        _meaning = (
            {
                "$or": [
                    {"meaning": {"$regex": re.escape(meaning)}},
                    {"amplifiedMeanings.meaning": {"$regex": re.escape(meaning)}},
                ]
            }
            if meaning
            else {}
        )
        _roots = {"roots": root} if root else {}
        _vowels = (
            {"amplifiedMeanings.vowels.value": vowelClass.split("/")}
            if vowelClass
            else {}
        )

        cursor = self._collection.aggregate(
            [
                {
                    "$match": {"$and": [_lemma, _meaning, _roots, _vowels]},
                }
            ]
        )
        return list(cursor)

    def query_by_lemma_prefix(self, query: str) -> Sequence:
        cursor = self._collection.aggregate(
            _create_lemma_search_pipeline(query),
            collation={"locale": "en", "strength": 1, "normalization": True},
        )

        return list(cursor)

    def update(self, word) -> None:
        self._collection.update_one({"_id": word["_id"]}, {"$set": word})

from typing import List, Sequence

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.application.suggestion_finder import LemmaRepository
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.mongo_collection import MongoCollection

COLLECTION = "fragments"


def aggregate_lemmas(word: str, is_normalized: bool) -> List[dict]:
    return [
        {
            "$match": {
                "text.lines.content": {
                    "$elemMatch": {
                        "cleanValue": word,
                        "uniqueLemma.0": {"$exists": True},
                    }
                }
            }
        },
        {"$project": {"lines": "$text.lines"}},
        {"$unwind": "$lines"},
        {"$project": {"tokens": "$lines.content"}},
        {"$unwind": "$tokens"},
        {
            "$unionWith": {
                "coll": "chapters",
                "pipeline": [
                    {"$unwind": "$lines"},
                    {"$project": {"variants": "$lines.variants"}},
                    {"$unwind": "$variants"},
                    {"$project": {"tokens": "$variants.reconstruction"}},
                    {"$unwind": "$tokens"},
                ],
            }
        },
        {
            "$unionWith": {
                "coll": "chapters",
                "pipeline": [
                    {"$unwind": "$lines"},
                    {"$project": {"variants": "$lines.variants"}},
                    {"$unwind": "$variants"},
                    {"$project": {"manuscripts": "$variants.manuscripts"}},
                    {"$unwind": "$manuscripts"},
                    {"$project": {"tokens": "$manuscripts.line.content"}},
                    {"$unwind": "$tokens"},
                ],
            }
        },
        {
            "$match": {
                "tokens.cleanValue": word,
                "tokens.normalized": is_normalized,
                "tokens.uniqueLemma.0": {"$exists": True},
            }
        },
        {"$group": {"_id": "$tokens.uniqueLemma", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]


class MongoLemmaRepository(LemmaRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def query_lemmas(self, word: str, is_normalized: bool) -> Sequence[Lemma]:
        cursor = self._collection.aggregate(aggregate_lemmas(word, is_normalized))
        return [
            [WordId(unique_lemma) for unique_lemma in result["_id"]]
            for result in cursor
        ]

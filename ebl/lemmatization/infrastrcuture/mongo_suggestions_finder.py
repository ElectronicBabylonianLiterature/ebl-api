from typing import Dict, List, Mapping, Sequence

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.application.suggestion_finder import LemmaRepository
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.mongo_collection import MongoCollection

COLLECTION = "fragments"


def aggregate_lemmas(words: Sequence[str], is_normalized: bool) -> List[dict]:
    is_requested_word = {"$in": list(words)}
    return [
        {
            "$match": {
                "text.lines.content": {
                    "$elemMatch": {
                        "cleanValue": is_requested_word,
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
                "tokens.cleanValue": is_requested_word,
                "tokens.normalized": is_normalized,
                "tokens.uniqueLemma.0": {"$exists": True},
            }
        },
        {
            "$group": {
                "_id": {"word": "$tokens.cleanValue", "lemma": "$tokens.uniqueLemma"},
                "count": {"$sum": 1},
            }
        },
    ]


def _rank(result: dict) -> tuple:
    return -result["count"], result["_id"]["lemma"]


class MongoLemmaRepository(LemmaRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def query_lemmas(self, word: str, is_normalized: bool) -> Sequence[Lemma]:
        return self.query_lemmas_of_words([word], is_normalized).get(word, [])

    def query_lemmas_of_words(
        self, words: Sequence[str], is_normalized: bool
    ) -> Mapping[str, Sequence[Lemma]]:
        cursor = self._collection.aggregate(aggregate_lemmas(words, is_normalized))
        lemmas: Dict[str, List[Lemma]] = {}
        for result in sorted(cursor, key=_rank):
            lemmas.setdefault(result["_id"]["word"], []).append(
                [WordId(unique_lemma) for unique_lemma in result["_id"]["lemma"]]
            )
        return lemmas

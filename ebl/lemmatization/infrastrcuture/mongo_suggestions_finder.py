from typing import Dict, List, Mapping, Sequence

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.application.suggestion_finder import LemmaRepository
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.mongo_collection import MongoCollection

COLLECTION = "fragments"


def _select(path: str, is_requested_word: dict) -> dict:
    return {"$match": {f"{path}.cleanValue": is_requested_word}}


def _unwind_chapter_tokens(
    arrays: Sequence[str], tokens: str, is_requested_word: dict
) -> dict:
    path = ".".join([*arrays, tokens])
    has_requested_word = _select(path, is_requested_word)
    return {
        "$unionWith": {
            "coll": "chapters",
            "pipeline": [
                has_requested_word,
                {"$project": {path: 1}},
                *(
                    stage
                    for depth in range(1, len(arrays) + 1)
                    for stage in (
                        {"$unwind": f"${'.'.join(arrays[:depth])}"},
                        has_requested_word,
                    )
                ),
                {"$project": {"tokens": f"${path}"}},
                {"$unwind": "$tokens"},
            ],
        }
    }


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
        _select("lines.content", is_requested_word),
        {"$project": {"tokens": "$lines.content"}},
        {"$unwind": "$tokens"},
        _unwind_chapter_tokens(
            ("lines", "variants"), "reconstruction", is_requested_word
        ),
        _unwind_chapter_tokens(
            ("lines", "variants", "manuscripts"), "line.content", is_requested_word
        ),
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

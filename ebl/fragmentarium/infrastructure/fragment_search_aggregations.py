from typing import Tuple, List
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from enum import Enum, auto


class SearchOperator(Enum):
    AND = "and"
    OR = "or"
    LINE = "line"
    PHRASE = "phrase"
    LEMMA = "lemma"

def get_matchers(_operator, lemmas) -> Tuple[dict, dict]:
    pass

def _flatten_vocabulary():
    return [
        {"$project": {"museumNumber": 1, "line": "$text.lines.content"}},
        {"$unwind": {"path": "$line", "includeArrayIndex": "lineIndex"}},
        {
            "$project": {
                "_id": 1,
                "lemmas": "$line.uniqueLemma",
                "lineIndex": 1,
                "tokenIndex": 1,
                "museumNumber": 1,
            }
        },
        {
            "$addFields": {
                "_vocabulary": {
                    "$setIntersection": {
                        "$reduce": {
                            "input": "$lemmas",
                            "initialValue": [],
                            "in": {"$concatArrays": ["$$value", "$$this"]},
                        }
                    }
                },
            }
        },
    ]


def _create_query_result():
    return [
        {
            "$group": {
                "_id": "$_id",
                "matchingLines": {"$push": "$lineIndex"},
                "museumNumber": {"$first": "$museumNumber"},
            }
        },
        {
            "$addFields": {
                "total": {"$size": "$matchingLines"},
            }
        },
        {
            "$group": {
                "_id": None,
                "totalMatchingLines": {"$sum": "$total"},
                "items": {"$push": "$$ROOT"},
            }
        },
        {"$project": {"_id": 0}},
    ]


def search_and_filter(line_match: dict, vocabulary_match: dict):
    return [
        {"$match": line_match},
        *_flatten_vocabulary(),
        {"$match": vocabulary_match},
        *_create_query_result(),
    ]


def simple_search(lemma: str) -> List[dict]:
    return [
        {"$match": {"text.lines.content.uniqueLemma": lemma}},
        *_flatten_vocabulary(),
        {"$match": {"_vocabulary": lemma}},
        *_create_query_result(),
    ]


def search_or(lemmas: List[str]) -> List[dict]:
    return [
        {
            "$match": {
                "$or": [{"text.lines.content.uniqueLemma": lemma} for lemma in lemmas]
            }
        },
        *_flatten_vocabulary(),
        {"$match": {"$or": [{"_vocabulary": lemma} for lemma in lemmas]}},
        *_create_query_result(),
    ]


def search_and(lemmas: List[str]) -> List[dict]:
    return [
        {"$match": {"text.lines.content.uniqueLemma": {"$all": lemmas}}},
        *_flatten_vocabulary(),
        {"$match": {"$or": [{"_vocabulary": lemma} for lemma in lemmas]}},
        *_create_query_result(),
    ]


def search_lines(lemmas: List[str]) -> List[dict]:
    return [
        {"$match": {"text.lines.content.uniqueLemma": {"$all": lemmas}}},
        *_flatten_vocabulary(),
        {"$match": {"_vocabulary": {"$all": lemmas}}},
        *_create_query_result(),
    ]

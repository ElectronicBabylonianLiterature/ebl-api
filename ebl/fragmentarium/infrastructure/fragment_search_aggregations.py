from typing import Tuple, List, Dict
from enum import Enum

VOCAB_PATH = "vocabulary"
LEMMA_PATH = "text.lines.content.uniqueLemma"


class QueryType(Enum):
    AND = "and"
    OR = "or"
    LINE = "line"
    PHRASE = "phrase"
    LEMMA = "lemma"


def _flatten_vocabulary() -> List[dict]:
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
                VOCAB_PATH: {
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


def _arrange_result() -> List[dict]:
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
        {"$sort": {"total": -1}},
        {
            "$group": {
                "_id": None,
                "totalMatchingLines": {"$sum": "$total"},
                "items": {"$push": "$$ROOT"},
            }
        },
        {"$project": {"_id": 0}},
    ]


def search_and_filter(line_matcher: dict, vocabulary_matcher: dict) -> List[dict]:
    return [
        {"$match": line_matcher},
        *_flatten_vocabulary(),
        {"$match": vocabulary_matcher},
        *_arrange_result(),
    ]


def create_search_aggregation(
    search_operator: QueryType, lemmas: List[str]
) -> List[dict]:
    matchers: Dict[QueryType, Tuple[dict, dict]] = {
        QueryType.LEMMA: (
            {LEMMA_PATH: lemmas[0]},
            {VOCAB_PATH: lemmas[0]},
        ),
        QueryType.AND: (
            {LEMMA_PATH: {"$all": lemmas}},
            {"$or": [{VOCAB_PATH: lemma} for lemma in lemmas]},
        ),
        QueryType.OR: (
            {"$or": [{LEMMA_PATH: lemma} for lemma in lemmas]},
            {"$or": [{VOCAB_PATH: lemma} for lemma in lemmas]},
        ),
        QueryType.LINE: (
            {LEMMA_PATH: {"$all": lemmas}},
            {VOCAB_PATH: {"$all": lemmas}},
        ),
        QueryType.PHRASE: (
            {LEMMA_PATH: {"$all": lemmas}},
            {VOCAB_PATH: {"$all": lemmas}},
        ),
    }

    return search_and_filter(*matchers[search_operator])

from typing import Tuple, List, Dict, Sequence, Optional
from enum import Enum
from ebl.fragmentarium.infrastructure.queries import number_is


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


def _arrange_result(include_lemma_sequences=False) -> List[dict]:
    return [
        {
            "$group": {
                "_id": "$_id",
                "matchingLines": {"$push": "$lineIndex"},
                "museumNumber": {"$first": "$museumNumber"},
                **(
                    {"lemmaSequences": {"$push": "$lemmas"}}
                    if include_lemma_sequences
                    else {}
                ),
                "matchCount": {"$sum": 1},
            }
        },
        {"$sort": {"matchCount": -1}},
        {
            "$group": {
                "_id": None,
                **(
                    {}
                    if include_lemma_sequences
                    else {"matchCountTotal": {"$sum": "$matchCount"}}
                ),
                "items": {"$push": "$$ROOT"},
            }
        },
        {"$project": {"_id": 0}},
    ]


def search_and_filter(
    line_matcher: dict, vocabulary_matcher: dict, include_lemma_sequences=False
) -> List[dict]:
    return [
        {"$match": line_matcher},
        *_flatten_vocabulary(),
        {"$match": vocabulary_matcher},
        *_arrange_result(include_lemma_sequences),
    ]


def create_search_aggregation(
    query_operator: QueryType, lemmas: Sequence[str]
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

    return search_and_filter(
        *matchers[query_operator],
        include_lemma_sequences=query_operator == QueryType.PHRASE,
    )


def _transliteration_line_match(line_patterns: List[str]) -> List[Dict]:
    pattern_length = len(line_patterns)
    return (
        [
            {
                "$addFields": {
                    "signChunks": {
                        "$zip": {
                            "inputs": [
                                "$signLines",
                                *(
                                    {
                                        "$slice": [
                                            "$signLines",
                                            i + 1,
                                            {"$size": "$signLines"},
                                        ]
                                    }
                                    for i in range(pattern_length - 1)
                                ),
                            ]
                        }
                    }
                }
            },
            {"$unwind": {"path": "$signChunks", "includeArrayIndex": "chunkIndex"}},
            {
                "$match": {
                    f"signChunks.{i}": {"$regex": line_pattern}
                    for i, line_pattern in enumerate(line_patterns)
                }
            },
        ]
        if pattern_length > 1
        else [
            {"$unwind": {"path": "$signLines", "includeArrayIndex": "chunkIndex"}},
            {
                "$match": {
                    "signLines": {"$regex": line_patterns[0]},
                }
            },
        ]
    )


def match_transliteration(transliteration: Optional[List[str]]) -> List[Dict]:
    if not transliteration:
        return []

    return [
        {
            "$project": {
                "museumNumber": True,
                "lineTypes": "$text.lines.type",
                "signs": True,
            }
        },
        {"$unwind": {"path": "$lineTypes", "includeArrayIndex": "lineIndex"}},
        {"$match": {"lineTypes": "TextLine"}},
        {
            "$group": {
                "_id": "$_id",
                "museumNumber": {"$first": "$museumNumber"},
                "textLines": {"$push": "$lineIndex"},
                "signLines": {"$first": {"$split": ["$signs", "\n"]}},
            }
        },
        *_transliteration_line_match(transliteration),
        {
            "$group": {
                "_id": "$_id",
                "museumNumber": {"$first": "$museumNumber"},
                "matchingLines": {
                    "$push": {"$arrayElemAt": ["$textLines", "$chunkIndex"]}
                },
                "matchCount": {"$sum": 1},
            }
        },
    ]


def transform_result() -> List[Dict]:
    return [
        {"$sort": {"matchCount": -1}},
        {
            "$group": {
                "_id": None,
                "items": {"$push": "$$ROOT"},
                "matchCountTotal": {"$sum": "$matchCount"},
            }
        },
        {"$project": {"_id": False}},
    ]


def prefilter_fragments(query: Dict) -> List[Dict]:
    number_query = number_is(query["number"]) if "number" in query else {}
    id_query = (
        {"references": {"$elemMatch": {"id": query["bibliographyId"]}}}
        if "bibliographyId" in query
        else {}
    )
    if "pages" in query:
        id_query["references"]["$elemMatch"]["pages"] = {
            "$regex": rf".*?(^|[^\d]){query['pages']}([^\d]|$).*?"
        }

    # TODO: accession? CDLI? Script?
    constraints = {**number_query, **id_query}
    return [{"$match": constraints}] if constraints else []


def create_query_aggregation(query) -> List[Dict]:
    return [
        *prefilter_fragments(query),
        *match_transliteration(query.get("transliteration")),
        # TODO: match lemmas here
        *transform_result(),
    ]

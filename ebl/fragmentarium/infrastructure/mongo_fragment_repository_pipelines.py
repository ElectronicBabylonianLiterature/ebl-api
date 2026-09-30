from typing import List, Optional, Sequence


def chapter_lemma_pipeline(clean_values: List[str]) -> List[dict]:
    return [
        {
            "$project": {
                "_id": 1,
                "lines.variants.reconstruction": {
                    "cleanValue": 1,
                    "uniqueLemma": 1,
                },
                "lines.variants.manuscripts.line.content": {
                    "cleanValue": 1,
                    "uniqueLemma": 1,
                },
            }
        },
        {"$unwind": "$lines"},
        {"$unwind": "$lines.variants"},
        {
            "$project": {
                "reconstruction": "$lines.variants.reconstruction",
                "manuscripts": "$lines.variants.manuscripts",
            }
        },
        {
            "$facet": {
                "reconstructionLemmas": [
                    {"$project": {"_id": False, "reconstruction": True}},
                    {"$unwind": "$reconstruction"},
                    {"$replaceRoot": {"newRoot": "$reconstruction"}},
                    {
                        "$match": {
                            "uniqueLemma.0": {"$exists": True},
                            "cleanValue": {"$in": clean_values},
                        }
                    },
                ],
                "manuscriptLemmas": [
                    {"$project": {"_id": False, "manuscripts": True}},
                    {"$unwind": "$manuscripts"},
                    {"$unwind": "$manuscripts.line.content"},
                    {"$replaceRoot": {"newRoot": "$manuscripts.line.content"}},
                    {
                        "$match": {
                            "uniqueLemma.0": {"$exists": True},
                            "cleanValue": {"$in": clean_values},
                        }
                    },
                ],
            }
        },
        {
            "$project": {
                "combinedLemmas": {
                    "$concatArrays": ["$reconstructionLemmas", "$manuscriptLemmas"]
                }
            }
        },
        {"$unwind": "$combinedLemmas"},
        {"$replaceRoot": {"newRoot": "$combinedLemmas"}},
    ]


def fragment_lemma_pipeline(clean_values: List[str]) -> List[dict]:
    return [
        {
            "$match": {
                "text.lines.content": {
                    "$elemMatch": {
                        "cleanValue": {"$in": clean_values},
                        "uniqueLemma.0": {"$exists": True},
                    }
                }
            }
        },
        {"$project": {"_id": False, "text.lines": True}},
        {"$unwind": "$text.lines"},
        {"$project": {"tokens": "$text.lines.content"}},
        {"$unwind": "$tokens"},
        {
            "$project": {
                "cleanValue": "$tokens.cleanValue",
                "uniqueLemma": "$tokens.uniqueLemma",
            }
        },
        {
            "$match": {
                "uniqueLemma.0": {"$exists": True},
                "cleanValue": {"$in": clean_values},
            }
        },
    ]


def aggregate_counts() -> List[dict]:
    return [
        {
            "$group": {
                "_id": {"cleanValue": "$cleanValue", "uniqueLemma": "$uniqueLemma"},
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "cleanValue": "$_id.cleanValue",
                "uniqueLemma": "$_id.uniqueLemma",
                "count": True,
            }
        },
        {"$sort": {"count": -1}},
        {
            "$group": {
                "_id": "$cleanValue",
                "lemmatizations": {
                    "$addToSet": {"uniqueLemma": "$uniqueLemma", "count": "$count"}
                },
            }
        },
    ]


def omit_text_lines() -> List:
    return [{"$addFields": {"text.lines": []}}]


def filter_fragment_lines(lines: Optional[Sequence[int]]) -> List:
    return (
        [
            {
                "$addFields": {
                    "text.lines": (
                        {
                            "$map": {
                                "input": lines,
                                "as": "i",
                                "in": {"$arrayElemAt": ["$text.lines", "$$i"]},
                            }
                        }
                    )
                }
            }
        ]
        if lines
        else []
    )

from typing import Set, Tuple, Optional, Sequence, List


def aggregate_ngram_overlaps(
    ngrams: Set[Tuple[str]], limit: Optional[int] = None
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
                                "$size": {"$setIntersection": ["$ngrams", ngram_list]}
                            },
                            "minLength": {
                                "$min": [
                                    {"$size": "$ngrams"},
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

    return pipeline

from typing import Dict, List

CORPUS_QUERY_SORT = {
    "matchCount": -1,
    "textId.genre": 1,
    "textId.category": 1,
    "textId.index": 1,
    "stage": 1,
    "name": 1,
    "_id": 1,
}


def paginated_corpus_result(query: Dict) -> List[Dict]:
    offset = query.get("offset", 0)
    return [
        {
            "$facet": {
                "items": [
                    {"$sort": CORPUS_QUERY_SORT},
                    *([{"$skip": offset}] if offset else []),
                    {"$limit": query["limit"]},
                    {"$project": {"_id": False}},
                ],
                "count": [
                    {
                        "$group": {
                            "_id": None,
                            "totalChapters": {"$sum": 1},
                            "matchCountTotal": {
                                "$sum": {"$ifNull": ["$matchCount", 0]}
                            },
                        }
                    }
                ],
            }
        },
        {
            "$project": {
                "_id": False,
                "items": True,
                "totalChapters": {
                    "$ifNull": [{"$arrayElemAt": ["$count.totalChapters", 0]}, 0]
                },
                "matchCountTotal": {
                    "$ifNull": [{"$arrayElemAt": ["$count.matchCountTotal", 0]}, 0]
                },
                "isMatchCountTotalExact": {"$literal": True},
            }
        },
        {
            "$addFields": {
                "hasNextPage": {
                    "$gt": ["$totalChapters", {"$add": [offset, {"$size": "$items"}]}]
                }
            }
        },
    ]

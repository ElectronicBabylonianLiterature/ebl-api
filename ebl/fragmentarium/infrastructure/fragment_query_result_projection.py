from typing import Dict, List

EXACT_COUNT = "exact"
PAGE_COUNT = "page"


def count_mode(query: Dict) -> str:
    return query.get("count", EXACT_COUNT)


def count_is_exact(query: Dict) -> bool:
    return count_mode(query) == EXACT_COUNT


def _limit_result(query: Dict) -> List[Dict]:
    limit = query["limit"]
    return [{"$limit": limit + 1 if count_mode(query) == PAGE_COUNT else limit}]


def _skip_result(query: Dict) -> List[Dict]:
    return [{"$skip": query["offset"]}] if query.get("offset") else []


def items_pipeline(query: Dict) -> List[Dict]:
    if "limit" in query:
        return [
            *_skip_result(query),
            *_limit_result(query),
            {
                "$project": {
                    "_id": True,
                    "matchCount": True,
                    "matchingLines": True,
                    "museumNumber": True,
                }
            },
        ]
    return [
        *_skip_result(query),
        {
            "$project": {
                "_id": False,
                "museumNumber": True,
                "matchingLines": True,
                "matchCount": True,
            }
        },
    ]


def count_pipeline() -> List[Dict]:
    return [
        {
            "$group": {
                "_id": None,
                "matchCountTotal": {"$sum": {"$ifNull": ["$matchCount", 0]}},
            }
        },
        {"$project": {"_id": False, "matchCountTotal": True}},
    ]


def _items_projection(query: Dict):
    if count_mode(query) == PAGE_COUNT and "limit" in query:
        return {"$slice": ["$items", query["limit"]]}
    return True


def _match_count_total_projection(query: Dict):
    if count_is_exact(query):
        return {
            "$ifNull": [
                {"$arrayElemAt": ["$count.matchCountTotal", 0]},
                0,
            ]
        }
    return {"$literal": None}


def _has_next_page_projection(query: Dict):
    if count_mode(query) == PAGE_COUNT:
        return (
            {"$gt": [{"$size": "$items"}, query["limit"]]}
            if "limit" in query
            else {"$literal": False}
        )
    return {"$literal": None}


def result_projection(query: Dict) -> Dict:
    return {
        "_id": False,
        "items": _items_projection(query),
        "matchCountTotal": _match_count_total_projection(query),
        "isMatchCountTotalExact": {"$literal": count_is_exact(query)},
        "hasNextPage": _has_next_page_projection(query),
    }

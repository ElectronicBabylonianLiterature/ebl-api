from typing import Any, Dict, Mapping, Optional

from ebl.bibliography.domain.bibliography_entry import (
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)
from ebl.bibliography.infrastructure.duplicate_candidate_queries import year_range

ACTIVE_BIBLIOGRAPHY_FILTER = {"deprecated": {"$ne": True}}


def expected_field_match(value: Any) -> Any:
    """Match exactly the stored value, distinguishing null from absent.

    A bare ``None`` also matches documents where the field is missing, which
    would let a concurrent removal slip past the compare-and-set.
    """
    return {"$type": "null"} if value is None else value


def server_owned_state_filter(
    id_: str, expected_server_owned_fields: Mapping[str, Any]
) -> Dict[str, Any]:
    return {
        "_id": id_,
        **{
            field: (
                expected_field_match(expected_server_owned_fields[field])
                if field in expected_server_owned_fields
                else {"$exists": False}
            )
            for field in sorted(SERVER_OWNED_BIBLIOGRAPHY_FIELDS)
        },
    }


def author_year_title_match(
    author: Optional[str], year: Optional[int], title: Optional[str]
) -> Dict[str, Any]:
    match: Dict[str, Any] = {}
    if author:
        match["author.0.family"] = author
    if year:
        match["issued.date-parts.0.0"] = year_range(year)
    if title:
        match["$expr"] = {"$eq": [{"$substrCP": ["$title", 0, len(title)]}, title]}
    return match


def bibliography_query_pipeline(
    match: Dict[str, Any], trailing_sort_field: str
) -> list[dict]:
    return [
        {"$match": {**match, **ACTIVE_BIBLIOGRAPHY_FILTER}},
        {"$addFields": {"primaryYear": primary_year_expression()}},
        {
            "$sort": {
                "author.0.family": 1,
                "primaryYear": 1,
                trailing_sort_field: 1,
            }
        },
        {"$project": {"primaryYear": 0}},
    ]


def primary_year_expression() -> dict:
    return {"$arrayElemAt": [{"$arrayElemAt": ["$issued.date-parts", 0]}, 0]}

from typing import Any, Dict, Optional, Sequence

import pymongo

from ebl.bibliography.application.partner_identity import normalize_partner_id
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.duplicate_audit import PROJECTION
from ebl.bibliography.infrastructure.duplicate_candidate_queries import (
    duplicate_candidate_queries,
    year_range,
)
from ebl.bibliography.application.serialization import (
    create_mongo_entry,
    create_object_entry,
)
from ebl.errors import DuplicateError, NotFoundError
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"
DUPLICATE_CANDIDATE_QUERY_MAX_TIME_MS = 5000
ACTIVE_BIBLIOGRAPHY_FILTER = {"deprecated": {"$ne": True}}


def join_reference_documents() -> Sequence[dict]:
    # This direct _id join intentionally does not follow deprecated bibliography
    # redirects. References with old duplicate IDs can still receive deprecated
    # documents until references are rewritten or this aggregation is redirect-aware.
    return [
        {"$unwind": {"path": "$references", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "bibliography",
                "localField": "references.id",
                "foreignField": "_id",
                "as": "references.document",
            }
        },
        {
            "$set": {
                "references.document": {"$arrayElemAt": ["$references.document", 0]}
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "references": {"$push": "$references"},
                "root": {"$first": "$$ROOT"},
            }
        },
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$root", {"references": "$references"}]}
            }
        },
        {
            "$set": {
                "references": {
                    "$filter": {
                        "input": "$references",
                        "as": "reference",
                        "cond": {"$ne": ["$$reference", {}]},
                    }
                }
            }
        },
    ]


class MongoBibliographyRepository(BibliographyRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        self._collection.create_index(
            [("citationKey", pymongo.ASCENDING)], unique=False
        )
        self._collection.create_index(
            [("aliases.value", pymongo.ASCENDING)], unique=False
        )
        self._collection.create_index(
            [("aliases.normalizedValue", pymongo.ASCENDING)], unique=False
        )

    def create(self, entry) -> str:
        mongo_entry = create_mongo_entry(entry)
        return self._collection.insert_one(mongo_entry)

    def query_by_id(self, id_: str) -> dict:
        data = self._collection.find_one_by_id(id_)
        return create_object_entry(data)

    def query_by_citation_key(self, citation_key: str) -> dict:
        data = self._collection.find_one({"citationKey": citation_key})
        return create_object_entry(data)

    def query_by_alias(self, alias: str) -> dict:
        normalized_alias = normalize_partner_id(alias)
        query = {"aliases.value": alias}
        if normalized_alias:
            query = {
                "$or": [
                    {"aliases.value": alias},
                    {"aliases.normalizedValue": normalized_alias},
                ]
            }
        data = list(self._collection.find_many(query))
        if not data:
            raise NotFoundError(f"bibliography alias {alias} not found.")
        if len({item["_id"] for item in data}) > 1:
            raise DuplicateError(f"bibliography alias {alias} is ambiguous.")
        return create_object_entry(data[0])

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[dict]:
        data = self._collection.find_many({"_id": {"$in": ids}})
        return [create_object_entry(item) for item in data]

    def update(self, entry) -> None:
        mongo_entry = create_mongo_entry(entry)
        self._collection.replace_one(mongo_entry)

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[dict]:
        return self._query(
            author_year_title_match(author, year, title),
            trailing_sort_field="title",
        )

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if container_title_short:
            match["container-title-short"] = container_title_short
        if collection_number:
            match["collection-number"] = collection_number
        return self._query(match, trailing_sort_field="collection-title")

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if title_short:
            match["title-short"] = title_short
        if volume:
            match["volume"] = volume
        return self._query(match, trailing_sort_field="collection-title")

    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        candidates: dict[str, dict] = {}
        for query in duplicate_candidate_queries(entry):
            cursor = self._collection.find_many(
                {"$and": [query, ACTIVE_BIBLIOGRAPHY_FILTER]}, projection=PROJECTION
            ).max_time_ms(DUPLICATE_CANDIDATE_QUERY_MAX_TIME_MS)
            for data in cursor.limit(limit):
                candidates[data["_id"]] = create_object_entry(data)
        return list(candidates.values())[:limit]

    def query_page(self, after: Optional[str], limit: int) -> Sequence[Any]:
        query: Dict[str, Any] = dict(ACTIVE_BIBLIOGRAPHY_FILTER)
        if after:
            query["_id"] = {"$gt": after}
        data = self._collection.find_many(query).sort("_id", 1).limit(limit)
        return [create_object_entry(item) for item in data]

    def _query(self, match: Dict[str, Any], trailing_sort_field: str) -> Sequence[dict]:
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                bibliography_query_pipeline(match, trailing_sort_field),
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def list_all_bibliography(self) -> Sequence[str]:
        return self._collection.get_all_values("_id", ACTIVE_BIBLIOGRAPHY_FILTER)


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
    return {
        "$arrayElemAt": [
            {"$arrayElemAt": ["$issued.date-parts", 0]},
            0,
        ]
    }

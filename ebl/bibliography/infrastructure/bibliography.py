from typing import Any, Dict, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.serialization import (
    create_mongo_entry,
    create_object_entry,
)
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"


def join_reference_documents() -> Sequence[dict]:
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

    def create(self, entry) -> str:
        mongo_entry = create_mongo_entry(entry)
        return self._collection.insert_one(mongo_entry)

    def query_by_id(self, id_: str) -> dict:
        data = self._collection.find_one_by_id(id_)
        return create_object_entry(data)

    def update(self, entry) -> None:
        mongo_entry = create_mongo_entry(entry)
        self._collection.replace_one(mongo_entry)

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}

        def pad_trailing_zeroes(year: int) -> int:
            padded_year = str(year).ljust(4, "0")
            return int(padded_year)

        if author:
            match["author.0.family"] = author
        if year:
            match["issued.date-parts.0.0"] = {
                "$gte": pad_trailing_zeroes(year),
                "$lt": pad_trailing_zeroes(year + 1),
            }
        if title:
            match["$expr"] = {"$eq": [{"$substrCP": ["$title", 0, len(title)]}, title]}
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                [
                    {"$match": match},
                    {
                        "$addFields": {
                            "primaryYear": {
                                "$arrayElemAt": [
                                    {"$arrayElemAt": ["$issued.date-parts", 0]},
                                    0,
                                ]
                            }
                        }
                    },
                    {"$sort": {"author.0.family": 1, "primaryYear": 1, "title": 1}},
                    {"$project": {"primaryYear": 0}},
                ],
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if container_title_short:
            match["container-title-short"] = container_title_short
        if collection_number:
            match["collection-number"] = collection_number
        return self._query(match)

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[dict]:
        match: Dict[str, Any] = {}
        if title_short:
            match["title-short"] = title_short
        if volume:
            match["volume"] = volume
        return self._query(match)

    def _query(self, match: Dict[str, Any]) -> Sequence[dict]:
        return [
            create_object_entry(data)
            for data in self._collection.aggregate(
                [
                    {"$match": match},
                    {
                        "$addFields": {
                            "primaryYear": {
                                "$arrayElemAt": [
                                    {"$arrayElemAt": ["$issued.date-parts", 0]},
                                    0,
                                ]
                            }
                        }
                    },
                    {
                        "$sort": {
                            "author.0.family": 1,
                            "primaryYear": 1,
                            "collection-title": 1,
                        }
                    },
                    {"$project": {"primaryYear": 0}},
                ],
                collation={"locale": "en", "strength": 1, "normalization": True},
            )
        ]

    def list_all_bibliography(self, query: Optional[dict] = None) -> Sequence[str]:
        return self._collection.get_all_values("_id", query)

    def list_all_indexed_bibliography(self) -> Sequence[str]:
        return [
            reference["_id"]
            for reference in self._collection.aggregate(
                [{"$match": {"is-indexed": True}}, {"$project": {"_id": True}}]
            )
        ]

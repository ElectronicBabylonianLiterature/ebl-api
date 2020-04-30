from typing import Any, Dict, Optional

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.serialization import (
    create_mongo_entry,
    create_object_entry,
)
from ebl.mongo_collection import MongoCollection

COLLECTION = "bibliography"


class MongoBibliographyRepository(BibliographyRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, entry) -> str:
        mongo_entry = create_mongo_entry(entry)
        return self._collection.insert_one(mongo_entry)

    def query_by_id(self, id_: str):
        data = self._collection.find_one_by_id(id_)
        return create_object_entry(data)

    def update(self, entry):
        mongo_entry = create_mongo_entry(entry)
        self._collection.replace_one(mongo_entry)

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[str], title: Optional[str]
    ):
        match: Dict[str, Any] = {}
        if author:
            match["author.0.family"] = author
        if year:
            match["issued.date-parts.0.0"] = year
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
                                    {"$arrayElemAt": ["$issued.date-parts", 0,]},
                                    0,
                                ]
                            }
                        }
                    },
                    {"$sort": {"author.0.family": 1, "primaryYear": 1, "title": 1,}},
                    {"$project": {"primaryYear": 0}},
                ],
                collation={"locale": "en", "strength": 1, "normalization": True,},
            )
        ]

import re
from typing import List, Sequence

from marshmallow import EXCLUDE
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema, AnnotationSchema
from ebl.fragmentarium.domain.annotation import Annotations, Annotation
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.mongo_collection import MongoCollection

COLLECTION = "annotations"


def has_none_values(dictionary: dict) -> bool:
    return not all(dictionary.values())


class MongoAnnotationsRepository(AnnotationsRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_or_update(self, annotations: Annotations) -> None:
        self._collection.replace_one(
            AnnotationsSchema().dump(annotations),
            {"fragmentNumber": str(annotations.fragment_number)},
            True,
        )

    def query_by_museum_number(self, number: MuseumNumber) -> Annotations:
        try:
            result = self._collection.find_one({"fragmentNumber": str(number)})

            return AnnotationsSchema().load(result, unknown=EXCLUDE)
        except NotFoundError:
            return Annotations(number)

    def retrieve_all(self) -> List[Annotations]:
        result = self._collection.find_many({})
        return AnnotationsSchema().load(result, unknown=EXCLUDE, many=True)

    def find_by_sign(self, sign: str) -> Sequence[Annotation]:
        query = {"$regex": re.escape(sign), "$options": "i"}
        result = self._collection.aggregate([
{"$match": {"annotations.data.signName": query}},
{"$project": {
    "fragmentNumber": 1,
    "annotations": {
        "$filter": {
            "input": "$annotations",
            "as": "annotation",
            "cond": {
                "$eq": ["$$annotation.data.signName", sign]
                }

    }},
}},
])
        """
        result = self._collection.aggregate([
{"$match": {"annotations.data.signName": query}},
{"$project": {
    "fragmentNumber": 1,
    "annotations": {
        "$filter": {
            "input": "$annotations",
            "as": "annotation",
            "cond": {
                 "$regexMatch": {
                                "input": "$$annotation.data.signName",
                                "regex": query
                 }
                }

    }},
}},
{"$unwind": "$annotations"},
])

"""
        return AnnotationsSchema().load(result, many=True, unknown=EXCLUDE)


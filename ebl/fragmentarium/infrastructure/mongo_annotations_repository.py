import re
from typing import Any, Dict, List, Optional, Sequence

from marshmallow import EXCLUDE
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import (
    AnnotationsWithScriptSchema,
    AnnotationsSchema,
)
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.mongo_collection import MongoCollection

COLLECTION = "annotations"


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

    def retrieve_all_non_empty(self) -> List[Annotations]:
        result = self._collection.find_many(
            {"annotations": {"$exists": True, "$ne": []}}
        )
        return AnnotationsSchema().load(result, unknown=EXCLUDE, many=True)

    def find_by_sign(
        self,
        sign: str,
        centroids_only: bool = False,
        cluster_id: Optional[str] = None,
        script_filter: Optional[str] = None,
    ) -> Sequence[Annotations]:
        query: Dict[str, str] = {"$regex": re.escape(sign), "$options": "i"}

        match_conditions: Dict[str, Any] = {"annotations.data.signName": query}

        annotation_filter_conditions: List[Dict[str, Any]] = [
            {"$eq": ["$$annotation.data.signName", sign]}
        ]

        if centroids_only:
            annotation_filter_conditions.append(
                {"$eq": ["$$annotation.pcaClustering.isCentroid", True]}
            )

        if cluster_id:
            annotation_filter_conditions.append(
                {"$eq": ["$$annotation.pcaClustering.clusterId", cluster_id]}
            )

        lookup_stages = [
            {
                "$lookup": {
                    "from": "fragments",
                    "localField": "fragmentNumber",
                    "foreignField": "_id",
                    "as": "fragment",
                }
            },
            {"$unwind": "$fragment"},
        ]

        if script_filter:
            match_conditions["fragment.script.period"] = script_filter
            pipeline = [
                *lookup_stages,
                {"$match": match_conditions},
            ]
        else:
            pipeline = [
                {"$match": match_conditions},
                *lookup_stages,
            ]

        pipeline.append(
            {
                "$project": {
                    "fragmentNumber": 1,
                    "annotations": {
                        "$filter": {
                            "input": "$annotations",
                            "as": "annotation",
                            "cond": {"$and": annotation_filter_conditions},
                        }
                    },
                    "script": "$fragment.script",
                    "provenance": "$fragment.archaeology.site",
                }
            }
        )

        result = self._collection.aggregate(pipeline)
        return AnnotationsWithScriptSchema().load(result, many=True, unknown=EXCLUDE)

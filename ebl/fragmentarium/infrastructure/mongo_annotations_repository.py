from marshmallow import EXCLUDE
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.annotation_repository import AnnotationRepository
from ebl.fragmentarium.application.annotation_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.mongo_collection import MongoCollection

COLLECTION = "annotations"


def has_none_values(dictionary: dict) -> bool:
    return not all(dictionary.values())


class MongoAnnotationsRepository(AnnotationRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_or_update(self, annotations: Annotations) -> None:
        self._collection.replace_one(
            AnnotationsSchema().dump(annotations),
            {"fragmentNumber": annotations.fragment_number},
            True,
        )

    def query_by_fragment_number(self, fragment_number: FragmentNumber) -> Annotations:
        try:
            result = self._collection.find_one({"fragmentNumber": fragment_number})

            return AnnotationsSchema().load(result, unknown=EXCLUDE)
        except NotFoundError:
            return Annotations(fragment_number)

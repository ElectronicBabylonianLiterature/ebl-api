from typing import Sequence

from pymongo.database import Database

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImageSchema
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
    CroppedSignImage,
)
from ebl.mongo_collection import MongoCollection

COLLECTION = "cropped_sign_images"


class MongoCroppedSignImagesRepository(CroppedSignImagesRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_many(self, cropped_sign_images: Sequence[CroppedSignImage]) -> None:
        schema = CroppedSignImageSchema(many=True)
        self._collection.insert_many(schema.dump(cropped_sign_images))

    def query_by_id(self, image_id: str) -> CroppedSignImage:
        return CroppedSignImageSchema().load(
            self._collection.find_one({"_id": image_id})
        )

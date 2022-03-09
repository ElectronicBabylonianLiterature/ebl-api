from typing import Sequence

from pymongo.database import Database

from ebl.fragmentarium.application.sign_images_repository import SignImagesRepository, CroppedSignImage, \
    CroppedSignImageSchema
from ebl.mongo_collection import MongoCollection

COLLECTION = "sign_images"


class MongoSignImagesRepository(SignImagesRepository):
    def __init__(self, database: Database) -> None:
        self._collection = MongoCollection(database, COLLECTION)

    def create_or_update(self, cropped_sign_image: Sequence[CroppedSignImage]) -> None:
        for element in cropped_sign_image:
            self._collection.replace_one(
                CroppedSignImageSchema().dump(element),
                True,
            )

    def query(self, sign_id: str) -> CroppedSignImage:
        return CroppedSignImageSchema().load(self._collection.find_one({"sign_id": sign_id}))






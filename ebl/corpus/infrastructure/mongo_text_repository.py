from typing import List

import pymongo

from ebl.corpus.application.corpus import COLLECTION, TextRepository
from ebl.corpus.application.text_serializer import deserialize, serialize
from ebl.corpus.domain.text import Text, TextId
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f"Text {id_.category}.{id_.index} not found.")


class MongoTextRepository(TextRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        self._collection.create_index(
            [("category", pymongo.ASCENDING), ("index", pymongo.ASCENDING)],
            unique=True,
        )

    def create(self, text: Text) -> None:
        self._collection.insert_one(serialize(text))

    def find(self, id_: TextId) -> Text:
        try:
            mongo_text = self._collection.find_one(
                {"category": id_.category, "index": id_.index}
            )
            return deserialize(mongo_text)
        except NotFoundError:
            raise text_not_found(id_)

    def list(self) -> List[Text]:
        return [
            deserialize(mongo_text) for mongo_text in self._collection.find_many({})
        ]

    def update(self, id_: TextId, text: Text) -> None:
        self._collection.update_one(
            {"category": id_.category, "index": id_.index}, {"$set": serialize(text)},
        )

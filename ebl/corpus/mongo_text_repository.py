from typing import List

import pymongo

from ebl.corpus.corpus import TextRepository, COLLECTION
from ebl.corpus.mongo_serializer import serialize, deserialize
from ebl.corpus.text import TextId, Text
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f'Text {id_.category}.{id_.index} not found.')


class MongoTextRepository(TextRepository):
    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

    def create_indexes(self) -> None:
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text: Text) -> None:
        self._mongo_repository.create(serialize(text))

    def find(self, id_: TextId) -> Text:
        mongo_text = self._find_one(id_)
        return deserialize(mongo_text)

    def list(self) -> List[Text]:
        return [deserialize(mongo_text)
                for mongo_text
                in self._mongo_collection.find()]

    def update(self, id_: TextId, text: Text) -> None:
        result = self._mongo_collection.update_one(
            {'category': id_.category, 'index': id_.index},
            {'$set': serialize(text)}
        )

        if result.matched_count == 0:
            raise text_not_found(id_)

    def _find_one(self, id_: TextId) -> dict:
        mongo_text = self._mongo_collection.find_one({
            'category': id_.category,
            'index': id_.index
        })

        if mongo_text:
            return mongo_text
        else:
            raise text_not_found(id_)

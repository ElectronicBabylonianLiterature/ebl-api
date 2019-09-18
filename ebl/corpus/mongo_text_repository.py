from typing import List

import pymongo

from ebl.corpus.corpus import COLLECTION, TextRepository
from ebl.corpus.mongo_serializer import deserialize, serialize
from ebl.corpus.text import Text, TextId
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f'Text {id_.category}.{id_.index} not found.')


class MongoTextRepository(MongoRepository, TextRepository):
    def __init__(self, database):
        MongoRepository.__init__(self, database, COLLECTION)

    def create_indexes(self) -> None:
        super()._create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text: Text) -> None:
        super()._insert_one(serialize(text))

    def find(self, id_: TextId) -> Text:
        try:
            mongo_text = super()._find_one({
                'category': id_.category,
                'index': id_.index
            })
            return deserialize(mongo_text)
        except NotFoundError:
            raise text_not_found(id_)

    def list(self) -> List[Text]:
        return [deserialize(mongo_text)
                for mongo_text
                in super()._find_many({})]

    def update(self, id_: TextId, text: Text) -> None:
        super()._update_one(
            {'category': id_.category, 'index': id_.index},
            {'$set': serialize(text)}
        )

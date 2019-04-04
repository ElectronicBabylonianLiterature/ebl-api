import pymongo
from ebl.corpus.text import Text
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'texts'


class MongoCorpus:

    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)

    def create_indexes(self):
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text, _=None):
        return self._mongo_repository.create(text.to_dict())

    def find(self, category, index):
        text = self._mongo_collection.find_one({
            'category': category,
            'index': index
        })

        if text is None:
            raise NotFoundError(f'Text {category}.{index} not found.')
        else:
            return Text.from_dict(text)

    def update(self, category, index, text, _=None):
        result = self._mongo_collection.update_one(
            {'category': category, 'index': index},
            {'$set': text.to_dict()}
        )

        if result.matched_count == 0:
            raise NotFoundError(f'Text {category}.{index} not found.')
        else:
            return self.find(text.category, text.index)

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

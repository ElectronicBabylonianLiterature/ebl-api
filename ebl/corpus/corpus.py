import pydash
import pymongo
from ebl.corpus.text import Text
from ebl.errors import NotFoundError, DataError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'texts'


def validate(text):
    duplicate_sigla = (
        pydash
        .chain(text.chapters)
        .flat_map(lambda chapter: chapter.manuscripts)
        .map_(lambda manuscript: manuscript.siglum)
        .map_(lambda siglum, _, sigla: (siglum, sigla.count(siglum)))
        .filter(lambda entry: entry[1] > 1)
        .map_(lambda entry: entry[0])
        .uniq()
        .value()
    )

    if duplicate_sigla:
        raise DataError(f'Duplicate sigla: {duplicate_sigla}.')


class MongoCorpus:

    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)

    def create_indexes(self):
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text, _=None):
        validate(text)
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
        validate(text)
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

import pymongo
from ebl.corpus.text import Text, Chapter, Classification, Stage
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

    def create(self, text):
        return self._mongo_repository.create(text.to_dict())

    def find(self, category, index):
        text = self._mongo_collection.find_one({
            'category': category,
            'index': index
        })

        if text is None:
            raise NotFoundError(f'Text {category}.{index} not found.')
        else:
            return Text(text['category'], text['index'], text['name'], tuple(
                Chapter(
                    Classification(chapter['classification']),
                    Stage.from_name(chapter['stage']),
                    chapter['number']
                )
                for chapter in text['chapters']
            ))

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

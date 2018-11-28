import re
import pymongo
from ebl.changelog import Changelog
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'words'
LEMMA_SEARCH_LIMIT = 5


class MongoDictionary(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)
        self._changelog = Changelog(database)

    def search(self, query):
        lemma = query.split(' ')
        cursor = self.get_collection().find({
            '$or': [
                {'lemma': lemma},
                {'forms': {'$elemMatch': {'lemma': lemma}}},
                {'meaning': {'$regex': re.escape(query)}}
            ]
        })

        return [word for word in cursor]

    def search_lemma(self, query):
        lemma = query.split(' ')
        cursor = self.get_collection().find({
            '$or': [
                {
                    f'{key}.{index}': {'$regex': f'^{re.escape(part)}'}
                    for index, part
                    in enumerate(lemma)
                }
                for key in ['lemma', 'forms.lemma']
            ]
        }).sort('_id', pymongo.ASCENDING).limit(LEMMA_SEARCH_LIMIT)

        return [word for word in cursor]

    def update(self, word, user):
        query = {'_id': word['_id']}
        old_word = self.get_collection().find_one(
            query
        )
        if old_word:
            self._changelog.create(
                COLLECTION,
                user.profile,
                old_word,
                word
            )
            self.get_collection().update_one(
                query,
                {'$set': word}
            )
        else:
            raise NotFoundError(f'Word {word["_id"]} not found.')

import re
import pydash
from ebl.changelog import Changelog
from ebl.mongo_repository import MongoRepository


COLLECTION = 'words'


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

    def update(self, word, user_profile):
        query = {'_id': word['_id']}
        old_word = self.get_collection().find_one(
            query
        )
        if old_word:
            self._changelog.create(
                COLLECTION,
                pydash.map_keys(user_profile,
                                lambda _, key: key.replace('.', '_')),
                old_word,
                word
            )
            self.get_collection().update_one(
                query,
                {'$set': word}
            )
        else:
            raise KeyError

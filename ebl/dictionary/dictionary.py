import re
from ebl.mongo_repository import MongoRepository


class MongoDictionary(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')

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

    def update(self, word):
        result = self.get_collection().update_one(
            {'_id': word['_id']},
            {'$set': word}
        )

        if result.matched_count == 0:
            raise KeyError

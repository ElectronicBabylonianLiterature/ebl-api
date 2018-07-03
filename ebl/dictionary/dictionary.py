import re


class MongoDictionary(object):

    def __init__(self, database):
        self.database = database

    def create(self, word):
        return self.database.words.insert_one(word).inserted_id

    def find(self, object_id):
        word = self.database.words.find_one({'_id': object_id})

        if word is None:
            raise KeyError
        else:
            return word

    def search(self, query):
        lemma = query.split(' ')
        cursor = self.database.words.find({
            '$or': [
                {'lemma': lemma},
                {'forms': {'$elemMatch': {'lemma': lemma}}},
                {'meaning': {'$regex': re.escape(query)}}
            ]
        })

        return [word for word in cursor]

    def update(self, word):
        result = self.database.words.update_one(
            {'_id': word['_id']},
            {'$set': word}
        )

        if result.matched_count == 0:
            raise KeyError

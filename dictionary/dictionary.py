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

    def search(self, lemma):
        cursor = self.database.words.find({
            '$or': [
                {'lemma': lemma},
                {'forms': {'$elemMatch': {'lemma': lemma}}}
            ]
        })

        return [word for word in cursor]

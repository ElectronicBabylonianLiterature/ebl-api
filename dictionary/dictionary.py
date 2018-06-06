class MongoDictionary(object):

    def __init__(self, client):
        self.database = client.dictionary

    def create(self, word):
        return self.database.words.insert_one(word).inserted_id

    def find(self, lemma, homonym):
        word = self.database.words.find_one({'lemma': lemma, 'homonym': homonym})

        if word is None:
            raise KeyError
        else:
            return word

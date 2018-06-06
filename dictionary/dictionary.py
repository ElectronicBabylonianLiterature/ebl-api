class Dictionary(object):

    def __init__(self, words):
        self.words = words

    def find(self, lemma, homonym):
        def is_match(word):
            return word['lemma'] == lemma and word['homonym'] == homonym

        matching_words = [word for word in self.words if is_match(word)]

        if matching_words:
            return matching_words[0]
        else:
            raise KeyError

class MongoDictionary(object):

    def __init__(self, client):
        self.database = client.dictionary

    def create(self, word):
        return self.database.words.insert_one(word).inserted_id

    def find(self, lemma, homonym):
        return self.database.words.find_one({'lemma': lemma, 'homonym': homonym})

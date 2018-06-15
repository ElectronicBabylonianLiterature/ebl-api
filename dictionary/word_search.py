import falcon

class WordSearch:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    @staticmethod
    def transform_object_id(word):
        result = dict(word)
        result['_id'] = str(word['_id'])
        return result

    def on_get(self, req, resp, lemma):
        compound_lemma = lemma.split(' ')
        words = self.dictionary.search(compound_lemma)
        resp.media = [self.transform_object_id(word) for word in words]

import falcon
from bson.json_util import dumps

class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, lemma, homonym):

        compound_lemma = lemma.split(' ')

        try:
            word = self.dictionary.find(compound_lemma, homonym)
            resp.media = dumps(word)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

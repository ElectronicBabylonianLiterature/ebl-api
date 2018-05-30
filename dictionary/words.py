import falcon

class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, lemma, homonym):

        compound_lemma = lemma.split(' ')

        try:
            resp.media = self.dictionary.find(compound_lemma, homonym)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

import falcon

class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, lemma, homonym):

        compound_lemma = lemma.split(' ')

        try:
            word = self.dictionary.find(compound_lemma, homonym)
            word.pop('_id', None)
            resp.media = word
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

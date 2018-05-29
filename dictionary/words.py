import falcon

class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, lemma, homonym):

        compoundLemma = lemma.split(' ')

        try:
             resp.media = self.dictionary.find(compoundLemma, homonym)
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND

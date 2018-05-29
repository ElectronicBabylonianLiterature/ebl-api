import falcon

class WordsResource:
    
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, lemma, homonym):

        compoundLemma = lemma.split(' ')
        words = [word for word in self.dictionary if word['lemma'] == compoundLemma and word['homonym'] == homonym]

        if(len(words) > 0):
            resp.media = words[0]
        else:
            resp.status = falcon.HTTP_NOT_FOUND

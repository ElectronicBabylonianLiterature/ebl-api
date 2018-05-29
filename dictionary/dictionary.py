class Dictionary(object):

    def __init__(self, words):
        self.words = words

    def find(self, lemma, homonym):
        matchingWords = [word for word in self.words if word['lemma'] == lemma and word['homonym'] == homonym]

        if(len(matchingWords) > 0):
            return matchingWords[0]
        else:
            raise KeyError

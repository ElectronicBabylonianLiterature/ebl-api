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

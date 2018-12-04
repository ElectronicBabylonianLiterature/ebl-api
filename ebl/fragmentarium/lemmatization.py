import copy
import json


class Lemmatization:
    def __init__(self, tokens):
        self._tokens = copy.deepcopy(tokens)

    def __eq__(self, other):
        return (isinstance(other, Lemmatization) and
                self._tokens == other.tokens)

    def __hash__(self):
        return hash(json.dumps(self._tokens))

    @property
    def tokens(self):
        return copy.deepcopy(self._tokens)

    @staticmethod
    def of_transliteration(transliteration):
        tokens = transliteration.tokenize(lambda value: {
            'value': value,
            'uniqueLemma': []
        })
        return Lemmatization(tokens)

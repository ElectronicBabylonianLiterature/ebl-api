import copy
import json
from ebl.fragmentarium.merger import Merger


class LemmatizationError(Exception):
    def __init__(self):
        super().__init__('Invalid lemmatization')


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

    @property
    def atf(self):
        return '\n'.join([
            ' '.join([token['value'] for token in row])
            for row in self._tokens
        ])

    def merge(self, transliteration):
        merged_tokens = Merger(lambda token: token['value'], 2).merge(
            self._tokens,
            self._tokenize(transliteration)
        )

        return Lemmatization(merged_tokens)

    @staticmethod
    def of_transliteration(transliteration):
        tokens = Lemmatization._tokenize(transliteration)
        return Lemmatization(tokens)

    @staticmethod
    def _tokenize(transliteration):
        return transliteration.tokenize(lambda value: {
            'value': value,
            'uniqueLemma': []
        })

    def is_compatible(self, other):
        def to_values(tokens):
            return [
                [
                    token['value']
                    for token in line
                ] for line in tokens
            ]

        return to_values(self._tokens) == to_values(other.tokens)

import copy
import json
import re
from ebl.fragmentarium.transliteration import IGNORE_LINE_PATTERN


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
        def create_token(value):
            return {
                'value': value,
                'uniqueLemma': []
            }

        lines = transliteration.atf.split('\n')
        tokens = [
            [
                create_token(value)
                for value in (
                    [line]
                    if re.match(IGNORE_LINE_PATTERN, line)
                    else line.split(' ')
                )
            ]
            for line in lines
        ]
        return Lemmatization(tokens)

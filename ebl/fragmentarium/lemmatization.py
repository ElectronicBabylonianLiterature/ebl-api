import copy
import difflib
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

    def merge(self, transliteration):
        merged_tokens = self._merge(
            self._tokens,
            self._tokenize(transliteration),
            self._diff(transliteration),
            True
        )

        return Lemmatization(merged_tokens)

    def _diff(self, transliteration):
        return difflib.ndiff(
            [
                ' '.join([token['value'] for token in line])
                for line in self._tokens
            ],
            transliteration.atf.splitlines(keepends=True)
        )

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

    @staticmethod
    def _merge(old, new, diff, recursive):
        result = []
        old_index = 0
        new_index = 0
        old_line = None

        for line in diff:
            prefix = line[:2]
            if prefix == '- ':
                old_line = old[old_index]
                old_index += 1
            elif prefix == '+ ':
                if recursive and old_line is not None:
                    inner_diff = difflib.ndiff(
                        [
                            token['value']
                            for token in old_line  # pylint: disable=E1133
                        ],
                        [
                            token['value']
                            for token in new[new_index]
                        ]
                    )
                    merged = Lemmatization._merge(
                        old_line,
                        new[new_index],
                        inner_diff,
                        False
                    )
                    result.append(merged)
                else:
                    result.append(new[new_index])
                new_index += 1
                old_line = None
            elif prefix == '  ':
                result.append(old[old_index])
                new_index += 1
                old_index += 1
                old_line = None
        return result

    def is_compatible(self, other):
        def to_values(tokens):
            return [
                [
                    token['value']
                    for token in line
                ] for line in tokens
            ]

        return to_values(self._tokens) == to_values(other.tokens)

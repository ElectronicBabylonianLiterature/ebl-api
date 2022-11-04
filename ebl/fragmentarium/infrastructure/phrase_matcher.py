from typing import Sequence


class PhraseMatcher:
    def __init__(self, phrase: Sequence[str]) -> None:
        self._phrase = phrase
        self._phrase_len = len(phrase)

    def _matches(self, subsequence: Sequence[str]) -> bool:
        return all(lemma in lemmas for lemma, lemmas in zip(self._phrase, subsequence))

    def matches(self, sequence: Sequence[Sequence[str]]) -> bool:
        sequence_len = len(sequence)

        if sequence_len < self._phrase_len:
            return False

        if sequence_len == self._phrase_len:
            return self._matches(sequence)

        for i in range(sequence_len - self._phrase_len + 1):
            subsequence = sequence[i : i + self._phrase_len]
            
            if self._matches(subsequence):
                return True

        return False
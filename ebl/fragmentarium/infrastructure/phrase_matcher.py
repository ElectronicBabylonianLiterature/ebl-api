from typing import Sequence, Iterable
from itertools import tee, dropwhile, product


LemmaLine = Sequence[Sequence[str]]


def ngrams(sequence: Iterable, n: int):
    iterables = tee(sequence, n)
    for i, sub_iterable in enumerate(iterables):
        for _ in range(i):
            next(sub_iterable, None)
    return zip(*iterables)


class PhraseMatcher:
    def __init__(self, phrase: Sequence[str]) -> None:
        self._phrase = tuple(phrase)
        self._phrase_len = len(phrase)

    def _is_match(self, line: LemmaLine) -> bool:
        return any(
            self._phrase == combination
            for combination in product(*(lemma or [""] for lemma in line))
        )

    def matches(self, line: LemmaLine) -> bool:
        line = list(
            dropwhile(lambda unique_lemmas: self._phrase[0] not in unique_lemmas, line)
        )

        for ngram in ngrams(line, self._phrase_len):
            if self._is_match(ngram):
                print(">>> matches")
                return True

            print(">>> doesn't match")
        return False


def filter_query_results(data: dict, phrase: Sequence[str]):

    phrase_matcher = PhraseMatcher(phrase)
    matching_items = []
    total_matching_lines = 0

    for query_item in data["items"]:
        lines = query_item["matchingLines"]
        lemma_sequences: Sequence[LemmaLine] = query_item["lemmaSequences"]
        total = 0
        matching_lines = []

        for i, sequence in zip(lines, lemma_sequences):
            if phrase_matcher.matches(sequence):
                matching_lines.append(i)
                total += 1

        if not matching_lines:
            continue

        query_item["matchingLines"] = matching_lines
        query_item["total"] = total

        del query_item["lemmaSequences"]

        total_matching_lines += total
        matching_items.append(query_item)

    data["items"] = matching_items
    data["totalMatchingLines"] = total_matching_lines

    return data

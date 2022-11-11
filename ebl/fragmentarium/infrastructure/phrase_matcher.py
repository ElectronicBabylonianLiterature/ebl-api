from typing import Sequence, Iterable, Tuple
from itertools import tee, dropwhile, product


LemmaSequence = Sequence[Sequence[str]]


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

    def _is_match(self, line: LemmaSequence) -> bool:
        return any(
            self._phrase == combination
            for combination in product(*(lemma or [""] for lemma in line))
        )

    def matches(self, line: LemmaSequence) -> bool:
        line = list(
            dropwhile(lambda unique_lemmas: self._phrase[0] not in unique_lemmas, line)
        )

        for ngram in ngrams(line, self._phrase_len):
            if self._is_match(ngram):
                return True

        return False


def get_matching_lines(
    lines: Sequence[int],
    lemma_sequences: Sequence[LemmaSequence],
    phrase_matcher: PhraseMatcher,
) -> Tuple[Sequence[int], int]:
    match_count = 0
    matching_lines = []

    for i, sequence in zip(lines, lemma_sequences):
        if phrase_matcher.matches(sequence):
            matching_lines.append(i)
            match_count += 1

    return matching_lines, match_count


def filter_query_results(data: dict, phrase: Sequence[str]):

    phrase_matcher = PhraseMatcher(phrase)
    matching_items = []
    match_count_total = 0

    for query_item in data["items"]:

        matching_lines, match_count = get_matching_lines(
            query_item["matchingLines"],
            query_item.pop("lemmaSequences"),
            phrase_matcher,
        )

        if match_count > 0:
            matching_items.append(
                {
                    **query_item,
                    "matchingLines": matching_lines,
                    "matchCount": match_count,
                }
            )

            match_count_total += match_count

    return {"items": matching_items, "matchCountTotal": match_count_total}

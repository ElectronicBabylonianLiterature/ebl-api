from typing import Sequence, Set, Tuple, TypeVar

from ebl.common.infrastructure.ngrams import DEFAULT_N

T = TypeVar("T")

N_VALUES = [
    DEFAULT_N,
    [1],
    [1, 2],
    [5],
]


def _ngrams(sequence: Sequence[T], n: int) -> Set[Tuple[T]]:
    return set(zip(*(sequence[i:] for i in range(n))))


def ngrams_from_signs(signs: str, N: Sequence[int]) -> Set[Tuple[str]]:
    split_signs = signs.replace("\n", " # ").split()
    all_ngrams = set.union(*(_ngrams(split_signs, n) for n in N))
    return {ngram for ngram in all_ngrams if "X" not in ngram}

from typing import Sequence, Set, Tuple, TypeVar, Optional
from ebl.corpus.domain.chapter import Chapter
from ebl.fragmentarium.domain.fragment import Fragment

T = TypeVar("T")


def _ngrams(sequence: Sequence[T], n: int) -> Set[Tuple[T]]:
    return set(zip(*(sequence[i:] for i in range(n))))


def ngrams_from_signs(signs: str, N: Sequence[int]) -> Set[Tuple[str]]:
    split_signs = signs.replace("\n", " # ").split()
    all_ngrams = set.union(*(_ngrams(split_signs, n) for n in N))
    return {ngram for ngram in all_ngrams if "X" not in ngram}


def chapter_ngrams_from_signs(
    chapter_signs: Sequence[Optional[str]], N: Sequence[int]
) -> Set[Tuple[str]]:
    return set.union(
        *(ngrams_from_signs(signs, N) for signs in chapter_signs if signs is not None)
    )


def compute_ngram_score(
    fragment: Fragment, chapter: Chapter, N: Sequence[int]
) -> float:
    F = ngrams_from_signs(fragment.signs, N)
    C = chapter_ngrams_from_signs(chapter.signs, N)

    return (len(F & C) / min(len(F), len(C))) if F and C else 0.0

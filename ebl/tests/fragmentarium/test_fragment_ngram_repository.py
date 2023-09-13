from typing import Sequence, Set, Tuple, TypeVar

import pytest
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema

T = TypeVar("T")


def ngrams(sequence: Sequence[T], n: int) -> Set[Tuple[T]]:
    return set(zip(*(sequence[i:] for i in range(n))))


def ngrams_from_signs(signs: str, N: Sequence[int]) -> Set[Tuple[str]]:
    split_signs = signs.replace("\n", " # ").split()
    all_ngrams = set.union(*(ngrams(split_signs, n) for n in N))
    return {ngram for ngram in all_ngrams if "X" not in ngram}


N_VALUES = [
    [1],
    [1, 2],
    [1, 2, 3],
    [5],
    [99],
]


@pytest.mark.parametrize(
    "N",
    N_VALUES,
)
@pytest.mark.parametrize(
    "N_NEW",
    N_VALUES,
)
def test_update_ngrams(fragment_repository, fragment_ngram_repository, N, N_NEW):
    fragment = TransliteratedFragmentFactory.build()
    number = MuseumNumberSchema().dump(fragment.number)
    fragment_id = fragment_repository.create(fragment)

    assert not fragment_ngram_repository._ngrams.exists({"_id": fragment_id})

    fragment_ngram_repository.update_ngrams(number, N)
    bigrams = ngrams_from_signs(fragment.signs, N)
    assert fragment_ngram_repository.get_ngrams(fragment_id) == bigrams

    fragment_ngram_repository.update_ngrams(number, N_NEW)
    bigrams = ngrams_from_signs(fragment.signs, N_NEW)
    assert fragment_ngram_repository.get_ngrams(fragment_id) == bigrams

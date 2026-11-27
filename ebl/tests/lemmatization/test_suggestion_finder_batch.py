from typing import Any, Callable

import pytest

from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.application.suggestion_finder import (
    LemmaQuery,
    SuggestionFinder,
)
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)
from ebl.tests.lemmatization.lemma_batch_support import EXPECTED_LEMMAS, QUERIES


@pytest.mark.parametrize("is_normalized", [False, True])
def test_query_lemmas_of_words(
    is_normalized: bool, lemma_repository: MongoLemmaRepository, seeded_tokens: None
) -> None:
    expected = {
        word: [list(lemma) for lemma in EXPECTED_LEMMAS[index]]
        for index, (word, flag) in enumerate(QUERIES)
        if flag == is_normalized and EXPECTED_LEMMAS[index]
    }

    lemmas = lemma_repository.query_lemmas_of_words(
        [word for word, _ in QUERIES], is_normalized
    )

    assert lemmas == expected
    assert expected


@pytest.mark.parametrize("index", range(len(QUERIES)))
def test_query_lemmas_counts_fragments_and_chapters(
    index: int, lemma_repository: MongoLemmaRepository, seeded_tokens: None
) -> None:
    assert lemma_repository.query_lemmas(*QUERIES[index]) == [
        list(lemma) for lemma in EXPECTED_LEMMAS[index]
    ]


def test_query_lemmas_of_no_words(
    lemma_repository: MongoLemmaRepository, seeded_tokens: None
) -> None:
    assert lemma_repository.query_lemmas_of_words([], False) == {}


def test_find_lemmas_of_many_looks_every_word_up_once(
    dictionary: Dictionary,
    word: dict,
    lemma_repository: MongoLemmaRepository,
    when: Callable[[object], Any],
) -> None:
    suggestion_finder = SuggestionFinder(dictionary, lemma_repository)
    other_word = {**word, "_id": "other I"}
    lemma = WordId(word["_id"])
    other_lemma = WordId(other_word["_id"])
    when(lemma_repository).query_lemmas_of_words(["GI₆", "ana"], False).thenReturn(
        {"GI₆": [[lemma, other_lemma], [lemma]], "ana": [[other_lemma]]}
    )
    when(lemma_repository).query_lemmas_of_words(["ana"], True).thenReturn({})
    when(dictionary).find_many([lemma, other_lemma]).thenReturn([other_word, word])

    assert suggestion_finder.find_lemmas_of_many(
        [
            LemmaQuery("GI₆", False),
            LemmaQuery("ana", True),
            LemmaQuery("ana", False),
            LemmaQuery("GI₆", False),
        ]
    ) == [
        [[word, other_word], [word]],
        [],
        [[other_word]],
        [[word, other_word], [word]],
    ]

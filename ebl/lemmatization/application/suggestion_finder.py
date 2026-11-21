from abc import ABC, abstractmethod
from typing import Dict, Mapping, Sequence

import attr

from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import Lemma

Suggestions = Sequence[Sequence[dict]]


@attr.s(auto_attribs=True, frozen=True)
class LemmaQuery:
    word: str
    is_normalized: bool


def _find_distinct_words(
    queries: Sequence[LemmaQuery], is_normalized: bool
) -> Sequence[str]:
    return list(
        dict.fromkeys(
            query.word for query in queries if query.is_normalized == is_normalized
        )
    )


class LemmaRepository(ABC):
    @abstractmethod
    def query_lemmas(self, word: str, is_normalized: bool) -> Sequence[Lemma]:
        raise NotImplementedError

    @abstractmethod
    def query_lemmas_of_words(
        self, words: Sequence[str], is_normalized: bool
    ) -> Mapping[str, Sequence[Lemma]]:
        raise NotImplementedError


class SuggestionFinder:
    def __init__(self, dictionary: Dictionary, repository: LemmaRepository) -> None:
        self._repository = repository
        self._dictionary = dictionary

    def find_lemmas(self, word: str, is_normalized: bool) -> Suggestions:
        return [
            [self._dictionary.find(unique_lemma) for unique_lemma in result]
            for result in self._repository.query_lemmas(word, is_normalized)
        ]

    def find_lemmas_of_many(
        self, queries: Sequence[LemmaQuery]
    ) -> Sequence[Suggestions]:
        results = self._query_lemmas_of_many(queries)
        words = self._find_words(results)
        return [
            [
                [
                    words.get(unique_lemma) or self._dictionary.find(unique_lemma)
                    for unique_lemma in lemma
                ]
                for lemma in result
            ]
            for result in results
        ]

    def _query_lemmas_of_many(
        self, queries: Sequence[LemmaQuery]
    ) -> Sequence[Sequence[Lemma]]:
        lemmas = {
            is_normalized: self._repository.query_lemmas_of_words(
                _find_distinct_words(queries, is_normalized), is_normalized
            )
            for is_normalized in dict.fromkeys(query.is_normalized for query in queries)
        }
        return [lemmas[query.is_normalized].get(query.word, []) for query in queries]

    def _find_words(self, results: Sequence[Sequence[Lemma]]) -> Dict[WordId, dict]:
        unique_lemmas = dict.fromkeys(
            unique_lemma
            for result in results
            for lemma in result
            for unique_lemma in lemma
        )
        return {
            word["_id"]: word
            for word in self._dictionary.find_many(list(unique_lemmas))
        }

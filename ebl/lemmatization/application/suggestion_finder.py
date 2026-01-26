from abc import ABC, abstractmethod
from typing import Sequence

from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.lemmatization.domain.lemmatization import Lemma


class LemmaRepository(ABC):
    @abstractmethod
    def query_lemmas(self, word: str, is_normalized: bool) -> Sequence[Lemma]: ...


class SuggestionFinder:
    def __init__(self, dictionary: Dictionary, repository: LemmaRepository) -> None:
        self._repository = repository
        self._dictionary = dictionary

    def find_lemmas(self, word: str, is_normalized: bool) -> Sequence[Sequence[dict]]:
        return [
            [self._dictionary.find(unique_lemma) for unique_lemma in result]
            for result in self._repository.query_lemmas(word, is_normalized)
        ]

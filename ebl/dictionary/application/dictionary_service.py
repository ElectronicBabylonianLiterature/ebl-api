from typing import Sequence

from ebl.changelog import Changelog
from ebl.dictionary.application.word_repository import WordRepository
from ebl.dictionary.domain.word import WordId
from ebl.users.domain.user import User
from ebl.common.query.query_collation import make_query_params_from_string

COLLECTION = "words"


class Dictionary:
    def __init__(self, repository: WordRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog

    def create(self, word) -> WordId:
        return self._repository.create(word)

    def find(self, id_):
        return self._repository.query_by_id(id_)

    def find_many(self, lemmas: Sequence[str]) -> Sequence:
        return self._repository.query_by_ids(lemmas)

    def search(self, query: str) -> Sequence:
        return self._repository.query_by_lemma_meaning_root_vowels(
            **{
                param.field: param
                for param in make_query_params_from_string(query)
                if param.value
            },
        )

    def search_lemma(self, lemma: str) -> Sequence:
        return self._repository.query_by_lemma_prefix(lemma)

    def list_all_words(self) -> Sequence[str]:
        return self._repository.list_all_words()

    def update(self, word, user: User) -> None:
        old_word = self.find(word["_id"])
        self._changelog.create(COLLECTION, user.profile, old_word, word)
        self._repository.update(word)

from typing import Sequence, Any
from urllib.parse import parse_qsl
from ebl.changelog import Changelog
from ebl.dictionary.application.word_repository import WordRepository
from ebl.dictionary.domain.word import WordId
from ebl.users.domain.user import User
from ebl.common.query.query_collation import make_query_params


COLLECTION = "words"


def get_search_params(query: str) -> dict[str, Any]:
    parsed_params = parse_qsl(query)
    vowel_class_values: list[tuple[str, ...]] = []
    other_params: dict[str, str] = {}
    for key, value in parsed_params:
        if key == "vowelClass":
            parts = tuple(
                vowel.strip()
                for vowel in value.replace(",", "/").split("/")
                if vowel.strip()
            )
            if parts:
                vowel_class_values.append(parts)
        else:
            other_params[key] = value
    result = {
        param.field: param for param in make_query_params(other_params) if param.value
    }
    if vowel_class_values:
        result["vowel_class"] = vowel_class_values
    return result


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
        params = get_search_params(query)
        return self._repository.query_by_lemma_meaning_root_vowels(
            word=params.get("word"),
            meaning=params.get("meaning"),
            root=params.get("root"),
            vowel_class=params.get("vowel_class"),
        )

    def search_lemma(self, lemma: str) -> Sequence:
        return self._repository.query_by_lemma_prefix(lemma)

    def list_all_words(self) -> Sequence[str]:
        return self._repository.list_all_words()

    def update(self, word, user: User) -> None:
        old_word = self.find(word["_id"])
        self._changelog.create(COLLECTION, user.profile, old_word, word)
        self._repository.update(word)

from typing import Sequence, Any
from urllib.parse import parse_qsl
from ebl.changelog import Changelog
from ebl.dictionary.application.word_repository import WordRepository
from ebl.dictionary.domain.word import WordId
from ebl.users.domain.user import User
from ebl.common.query.query_collation import make_query_params


COLLECTION = "words"


def _parse_vowel_class_value(value: str) -> tuple[str, ...]:
    parts = tuple(
        vowel.strip() for vowel in value.replace(",", "/").split("/") if vowel.strip()
    )
    return parts


def _parse_origin_value(value: str) -> list[str]:
    if "," in value:
        return value.split(",")
    return [value]


def _collect_parsed_params(
    parsed_params: list[tuple[str, str]],
) -> tuple[list[tuple[str, ...]], list[str], dict[str, str]]:
    vowel_class_values: list[tuple[str, ...]] = []
    origin_values: list[str] = []
    other_params: dict[str, str] = {}
    for key, value in parsed_params:
        if key == "vowelClass":
            parts = _parse_vowel_class_value(value)
            if parts:
                vowel_class_values.append(parts)
        elif key == "origin":
            origin_values.extend(_parse_origin_value(value))
        elif key == "query":
            other_params["word"] = value
        else:
            other_params[key] = value
    return vowel_class_values, origin_values, other_params


def _build_search_result(
    vowel_class_values: list[tuple[str, ...]],
    origin_values: list[str],
    other_params: dict[str, str],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        param.field: param for param in make_query_params(other_params) if param.value
    }
    if vowel_class_values:
        result["vowel_class"] = vowel_class_values
    if result:
        result["origin"] = origin_values if origin_values else []
    return result


def get_search_params(query: str) -> dict[str, Any]:
    parsed_params = parse_qsl(query)
    vowel_class_values, origin_values, other_params = _collect_parsed_params(
        parsed_params
    )
    return _build_search_result(vowel_class_values, origin_values, other_params)


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
            origin=params.get("origin"),
        )

    def search_lemma(self, lemma: str) -> Sequence:
        return self._repository.query_by_lemma_prefix(lemma)

    def list_all_words(self) -> Sequence[str]:
        return self._repository.list_all_words()

    def update(self, word, user: User) -> None:
        old_word = self.find(word["_id"])
        self._changelog.create(COLLECTION, user.profile, old_word, word)
        self._repository.update(word)

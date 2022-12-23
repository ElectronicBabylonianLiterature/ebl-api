import pydash
import pytest
import copy

from typing import Dict
from urllib.parse import urlencode
from ebl.dictionary.domain.dictionary_query import DictionaryFieldQuery
from ebl.errors import NotFoundError
from ebl.dictionary.domain.dictionary_query import make_query_params_from_string

COLLECTION = "words"


def _make_query_params(query: Dict) -> Dict[str, DictionaryFieldQuery]:
    return {
        param.field: param
        for param in make_query_params_from_string(urlencode(query))
        if param.value
    }


def test_create(database, word_repository, word):
    word_id = word_repository.create(word)

    assert database[COLLECTION].find_one({"_id": word_id}) == word


def test_find(database, word_repository, word):
    database[COLLECTION].insert_one(word)

    assert word_repository.query_by_id(word["_id"]) == word


def test_find_many(database, word_repository, word):
    another_word = {**word, "_id": "part1 part2 II"}
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_ids([word["_id"], another_word["_id"]]) == [
        word,
        another_word,
    ]


def test_word_not_found(word_repository):
    with pytest.raises(NotFoundError):
        word_repository.query_by_id("not found")


def test_search_finds_all_homonyms(database, word_repository, word):
    another_word = {**word, "_id": "part1 part2 II", "homonym": "II"}
    database[COLLECTION].insert_many([word, another_word])
    query = {"word": word["lemma"][0]}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [
        word,
        another_word,
    ]


def test_search_finds_by_meaning(database, word_repository, word):
    another_word = {
        **word,
        "_id": "part1 part2 II",
        "homonym": "II",
        "meaning": "not matching",
    }
    database[COLLECTION].insert_many([word, another_word])
    query = {"meaning": word["meaning"]}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [word]


def test_search_finds_by_root(database, word_repository, word):
    another_word = copy.deepcopy(
        {
            **word,
            "_id": "part1 part2 II",
            "homonym": "II",
        }
    )
    another_word["roots"][0] = "lmm"
    database[COLLECTION].insert_many([word, another_word])
    query = {"root": word["roots"][0]}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [word]


def test_search_finds_by_vowel_class(database, word_repository, word):
    another_word = copy.deepcopy(
        {
            **word,
            "_id": "part1 part2 II",
            "homonym": "II",
        }
    )
    another_word["amplifiedMeanings"][0]["vowels"][0]["value"] = ["e", "u"]
    database[COLLECTION].insert_many([word, another_word])
    query = {"vowelClass": "/".join(word["amplifiedMeanings"][0]["vowels"][0]["value"])}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [word]


def test_search_finds_by_all_params(database, word_repository, word):
    another_word = copy.deepcopy({**word, "_id": "part1 part2 II", "homonym": "II"})
    another_word["roots"][0] = "lmm"
    database[COLLECTION].insert_many([word, another_word])
    query = {
        "word": word["lemma"][0],
        "meaning": word["meaning"],
        "root": word["roots"][0],
        "vowelClass": "/".join(word["amplifiedMeanings"][0]["vowels"][0]["value"]),
    }

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [word]


def test_search_finds_duplicates(database, word_repository, word):
    another_word = {**word, "_id": "part1 part2 II", "homonym": "II"}
    database[COLLECTION].insert_many([word, another_word])
    query = {"meaning": word["meaning"][1:4]}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [
        word,
        another_word,
    ]


def test_search_not_found(word_repository):
    query = {"word": "lemma"}
    assert (
        word_repository.query_by_lemma_meaning_root_vowels(**_make_query_params(query))
        == []
    )


def test_update(word_repository, word):
    new_lemma = ["new"]
    word_id = word_repository.create(word)
    updated_word = pydash.defaults({"lemma": new_lemma}, word)

    word_repository.update(updated_word)

    assert word_repository.query_by_id(word_id) == updated_word

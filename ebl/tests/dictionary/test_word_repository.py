import pydash
import pytest
import copy

from typing import Dict, Any
from ebl.errors import NotFoundError

COLLECTION = "words"


def _make_query_params(query: Dict) -> Dict[str, Any]:
    query = dict(query)
    vowel_class_values: list[tuple[str, ...]] = []
    if "vowelClass" in query:
        parts = tuple(
            vowel.strip()
            for vowel in query.pop("vowelClass").replace(",", "/").split("/")
            if vowel.strip()
        )
        if parts:
            vowel_class_values.append(parts)
    from ebl.common.query.query_collation import make_query_params

    params: Dict[str, Any] = {}
    for param in make_query_params(query):
        if param.value:
            params[param.field] = param

    if vowel_class_values:
        params["vowel_class"] = vowel_class_values

    return params


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


@pytest.mark.parametrize(
    "query",
    [
        "part1",
        "pārT2",
        "pa?t1",
        "*rt*",
    ],
)
def test_search_finds_all_homonyms(database, word, word_repository, query):
    another_word = {**word, "_id": "part1 part2 II", "homonym": "II"}
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params({"word": query})
    ) == [
        word,
        another_word,
    ]


@pytest.mark.parametrize(
    "query",
    [
        "some semantics",
        "me semant",
        "sEmaNṭ",
    ],
)
def test_search_finds_by_meaning(database, word_repository, word, query):
    another_word = {
        **word,
        "_id": "part1 part2 II",
        "homonym": "II",
        "meaning": "not matching",
    }
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params({"meaning": query})
    ) == [word]


@pytest.mark.parametrize(
    "query",
    [
        "wb'",
        "w?'",
        "w*",
        "?b*",
        "*b*",
        '"*š"',
    ],
)
def test_search_finds_by_root(database, word_repository, word, query):
    another_word = copy.deepcopy(
        {
            **word,
            "_id": "part1 part2 II",
            "homonym": "II",
        }
    )
    another_word["roots"] = ["lmm", "plt", "prs"]
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params({"root": query})
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
    query = {"vowelClass": ",".join(word["amplifiedMeanings"][0]["vowels"][0]["value"])}

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **_make_query_params(query)
    ) == [word]


def test_search_finds_by_all_params(database, word_repository, word):
    another_word = copy.deepcopy({**word, "_id": "part1 part2 II", "homonym": "II"})
    another_word["roots"][0] = "lmm"
    database[COLLECTION].insert_many([word, another_word])
    query = {
        "word": '"Parṭ2"',
        "meaning": word["meaning"],
        "root": word["roots"][0],
        "vowelClass": ",".join(word["amplifiedMeanings"][0]["vowels"][0]["value"]),
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


def test_search_filters_by_origin(database, word, word_repository):
    another_word = {**word, "_id": "part1 part2 II", "origin": ["EBL"]}
    database[COLLECTION].insert_many([word, another_word])

    params = _make_query_params({"word": "part"})

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["CDA"]
    ) == [word]
    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["EBL"]
    ) == [another_word]
    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["CDA", "EBL"]
    ) == [word, another_word]

def test_search_filters_by_multiple_origins_in_single_word(database, word, word_repository):
    word_with_multiple_origins = {**word, "origin": ["CDA", "EBL"]}
    database[COLLECTION].insert_one(word_with_multiple_origins)

    params = _make_query_params({"word": "part"})

    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["CDA"]
    ) == [word_with_multiple_origins]
    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["EBL"]
    ) == [word_with_multiple_origins]
    assert word_repository.query_by_lemma_meaning_root_vowels(
        **params, origin=["SAD"]
    ) == []

def test_update(word_repository, word):
    new_lemma = ["new"]
    word_id = word_repository.create(word)
    updated_word = pydash.defaults({"lemma": new_lemma}, word)

    word_repository.update(updated_word)

    assert word_repository.query_by_id(word_id) == updated_word

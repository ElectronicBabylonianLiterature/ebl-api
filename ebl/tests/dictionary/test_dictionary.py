import pydash
import pytest
from freezegun import freeze_time

from ebl.errors import NotFoundError
from urllib.parse import urlencode
import copy

COLLECTION = "words"


def test_list_all_words(database, dictionary, word) -> None:
    dictionary.create(word)
    assert dictionary.list_all_words() == [word["_id"]]


def test_create_and_find(database, dictionary, word) -> None:
    word_id = dictionary.create(word)

    assert dictionary.find(word_id) == word


def test_create_and_find_many(database, dictionary, word, when) -> None:
    another_word = {**word, "_id": "part1 part2 II"}
    dictionary.create(word)
    dictionary.create(another_word)

    ids = [word["_id"], another_word["_id"]]

    assert dictionary.find_many(ids) == [
        word,
        another_word,
    ]

    when(dictionary).find_many(ids).thenReturn(
        [
            word,
            another_word,
        ]
    )
    assert dictionary.find_many(ids) == [
        word,
        another_word,
    ]


def test_word_not_found(dictionary):
    with pytest.raises(NotFoundError):
        dictionary.find("not found")


@pytest.mark.parametrize(
    "query",
    [
        "part1",
        "pārT2",
        "pa?t1",
        "*rt*",
    ],
)
def test_search_finds_all_homonyms(dictionary, word, query) -> None:
    another_word = {**word, "_id": "part1 part2 II", "homonym": "II"}
    dictionary.create(word)
    dictionary.create(another_word)

    assert dictionary.search(urlencode({"word": query})) == [word, another_word]


@pytest.mark.parametrize(
    "query",
    [
        "some semantics",
        "me semant",
        "sEmaNṭ",
    ],
)
def test_search_finds_by_meaning(dictionary, word, query) -> None:
    another_word = {
        **word,
        "_id": "part1 part2 II",
        "homonym": "II",
        "meaning": "not matching",
    }
    dictionary.create(word)
    dictionary.create(another_word)

    assert dictionary.search(urlencode({"meaning": query})) == [word]


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
def test_search_finds_by_root(dictionary, word, query) -> None:
    another_word = copy.deepcopy({**word, "_id": "part1 part2 II", "homonym": "II"})
    another_word["roots"] = ["lmm", "plt", "prs"]
    dictionary.create(word)
    dictionary.create(another_word)

    assert dictionary.search(urlencode({"root": query})) == [word]


def test_search_finds_by_vowel_class(dictionary, word):
    another_word = copy.deepcopy({**word, "_id": "part1 part2 II", "homonym": "II"})
    another_word["amplifiedMeanings"][0]["vowels"][0]["value"] = ["e", "u"]
    dictionary.create(word)
    dictionary.create(another_word)
    query = urlencode(
        {"vowelClass": ",".join(word["amplifiedMeanings"][0]["vowels"][0]["value"])},
    )

    assert dictionary.search(query) == [word]


def test_search_finds_by_all_params(dictionary, word) -> None:
    another_word = copy.deepcopy({**word, "_id": "part1 part2 II", "homonym": "II"})
    another_word["roots"][0] = "lmm"
    dictionary.create(word)
    dictionary.create(another_word)
    query = urlencode(
        {
            "word": '"Parṭ2"',
            "meaning": word["meaning"],
            "root": word["roots"][0],
            "vowelClass": ",".join(word["amplifiedMeanings"][0]["vowels"][0]["value"]),
        },
    )

    assert dictionary.search(query) == [word]


def test_search_finds_duplicates(dictionary, word) -> None:
    another_word = {**word, "_id": "part1 part2 II", "homonym": "II"}
    dictionary.create(word)
    dictionary.create(another_word)
    query = urlencode({"meaning": word["meaning"][1:4]})

    assert dictionary.search(query) == [word, another_word]


def test_search_not_found(dictionary) -> None:
    query = urlencode({"word": "lemma"})
    assert dictionary.search(query) == []


def test_search_filters_by_origin(dictionary, word) -> None:
    another_word = {**word, "_id": "part1 part2 II", "origin": "EBL"}
    dictionary.create(word)
    dictionary.create(another_word)

    query = urlencode({"word": "part", "origin": "CDA"})
    assert dictionary.search(query) == [word]

    query = urlencode({"word": "part", "origin": "EBL"})
    assert dictionary.search(query) == [another_word]


def test_search_defaults_to_cda_origin(dictionary, word) -> None:
    another_word = {**word, "_id": "part1 part2 II", "origin": "EBL"}
    dictionary.create(word)
    dictionary.create(another_word)

    query = urlencode({"word": "part"})
    assert dictionary.search(query) == [word, another_word]


def test_update(dictionary, word, user) -> None:
    new_lemma = ["new"]
    word_id = dictionary.create(word)
    updated_word = pydash.defaults({"lemma": new_lemma}, word)

    dictionary.update(updated_word, user)

    assert dictionary.find(word_id) == updated_word


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(dictionary, word, user, database, make_changelog_entry):
    word_id = dictionary.create(word)
    updated_word = pydash.defaults({"lemma": ["new"]}, word)
    dictionary.update(updated_word, user)

    expected_changelog = make_changelog_entry(COLLECTION, word_id, word, updated_word)
    assert (
        database["changelog"].find_one({"resource_id": word_id}, {"_id": 0})
        == expected_changelog
    )


def test_update_word_not_found(dictionary, word, user):
    with pytest.raises(NotFoundError):
        dictionary.update(pydash.defaults({"_id": "not found"}, word), user)

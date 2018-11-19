from bson.objectid import ObjectId
from freezegun import freeze_time
import pydash
import pytest


COLLECTION = 'words'


def test_create(database, dictionary, word):
    word_id = dictionary.create(word)

    assert database[COLLECTION].find_one({'_id': word_id}) == word


def test_find(database, dictionary, word):
    database[COLLECTION].insert_one(word)

    assert dictionary.find(word['_id']) == word


def test_word_not_found(dictionary):
    with pytest.raises(KeyError):
        dictionary.find(ObjectId())


def test_search_finds_all_homonyms(database, dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert dictionary.search(' '.join(word['lemma'])) == [word, another_word]


def test_search_finds_by_meaning(database, dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II',
        'meaning': 'not matching'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert dictionary.search(word['meaning'][1:4]) == [word]


def test_search_finds_duplicates(database, dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert dictionary.search(word['meaning'][1:4]) == [word, another_word]


def test_search_not_found(dictionary):
    assert dictionary.search('lemma') == []


def test_update(dictionary, word, user):
    new_lemma = ['new']
    word_id = dictionary.create(word)
    updated_word = pydash.defaults({'lemma': new_lemma}, word)

    dictionary.update(updated_word, user)

    assert dictionary.find(word_id) == updated_word


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(dictionary,
                   word,
                   user,
                   database,
                   make_changelog_entry):
    word_id = dictionary.create(word)
    updated_word = pydash.defaults({'lemma': ['new']}, word)
    dictionary.update(updated_word, user)

    expected_changelog = make_changelog_entry(
        COLLECTION,
        word_id,
        word,
        updated_word
    )
    assert database['changelog'].find_one(
        {'resource_id': word_id},
        {'_id': 0}
    ) == expected_changelog


def test_update_word_not_found(dictionary, word, user):
    with pytest.raises(KeyError):
        dictionary.update(pydash.defaults({'_id': ObjectId()}, word), user)

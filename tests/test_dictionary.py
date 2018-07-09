from bson.objectid import ObjectId
import pydash
import pytest


collection = 'words'

def test_create(database, dictionary, word):
    word_id = dictionary.create(word)

    assert database[collection].find_one({'_id': word_id}) == word

def test_find(database, dictionary, word):
    database[collection].insert_one(word).inserted_id

    assert dictionary.find(word['_id']) == word


def test_word_not_found(dictionary):
    with pytest.raises(KeyError):
        dictionary.find(ObjectId())


def test_search_finds_all_homonyms(database, dictionary, word):
    another_word = pydash.defaults({'homonym': 'II'}, word)
    database[collection].insert_many([word, another_word])

    assert dictionary.search(' '.join(word['lemma'])) == [word, another_word]


def test_search_finds_by_meaning(database, dictionary, word):
    another_word = pydash.defaults({'meaning': 'not matching'}, word)
    database[collection].insert_many([word, another_word])

    assert dictionary.search(word['meaning'][1:4]) == [word]


def test_search_finds_duplicates(database, dictionary, word):
    another_word = pydash.clone_deep(word)
    database[collection].insert_many([word, another_word])

    assert dictionary.search(' '.join(word['lemma'])) == [word, another_word]


def test_search_not_found(dictionary):
    assert dictionary.search('lemma') == []


def test_update(dictionary, word):
    new_lemma = ['new']
    word_id = dictionary.create(word)
    updated_word = pydash.defaults({'lemma': new_lemma}, word)

    dictionary.update(updated_word)

    assert dictionary.find(word_id) == updated_word


def test_update_word_not_found(dictionary, word):
    with pytest.raises(KeyError):
        dictionary.update(pydash.defaults({'_id': ObjectId()}, word))

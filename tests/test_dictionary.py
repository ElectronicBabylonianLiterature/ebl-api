from bson.objectid import ObjectId
import pytest
import mongomock

from dictionary.dictionary import MongoDictionary

@pytest.fixture
def dictionary():
    return MongoDictionary(mongomock.MongoClient().dictionary)

def test_create_and_find(dictionary):
    lemma = ['part1', 'part2']
    homonym = 'I'

    word = {
        'lemma': lemma,
        'homonym': homonym
    }

    word_id = dictionary.create(word)

    expected_word = {
        '_id': word_id,
        'lemma': lemma,
        'homonym': homonym
    }

    assert dictionary.find(word_id) == expected_word

def test_word_not_found(dictionary):
    with pytest.raises(KeyError):
        dictionary.find(ObjectId())

def test_search_finds_all_homonyms(dictionary):
    lemma = ['part1', 'part2']

    word1 = {
        'lemma': lemma,
        'homonym': 'I'
    }
    dictionary.create(word1)

    word2 = {
        'lemma': lemma,
        'homonym': 'II'
    }
    dictionary.create(word2)

    assert dictionary.search(' '.join(lemma)) == [word1, word2]

def test_search_finds_by_meaning(dictionary):
    word1 = {
        'lemma': ['lemma'],
        'meaning': 'meaning',
        'homonym': 'I'
    }
    dictionary.create(word1)

    word2 = {
        'lemma': ['lemma'],
        'meaning': 'not matching',
        'homonym': 'II'
    }
    dictionary.create(word2)

    assert dictionary.search(word1['meaning'][1:4]) == [word1]

def test_search_finds_duplicates(dictionary):
    lemma = ['part1', 'part2']
    homonym = 'I'

    word1 = {
        'lemma': lemma,
        'homonym': homonym
    }
    dictionary.create(word1)

    word2 = {
        'lemma': lemma,
        'homonym': homonym
    }
    dictionary.create(word2)

    assert dictionary.search(' '.join(lemma)) == [word1, word2]

def test_search_not_found(dictionary):
    assert dictionary.search('lemma') == []

def test_update(dictionary):
    lemma = ['part1', 'part2']
    new_lemma = ['new']
    homonym = 'I'

    word = {
        'lemma': lemma,
        'homonym': homonym
    }

    word_id = dictionary.create(word)

    updated_word = {
        '_id': word_id,
        'lemma': new_lemma,
        'homonym': homonym
    }

    dictionary.update(updated_word)

    assert dictionary.find(word_id) == updated_word

def test_update_word_not_found(dictionary):
    word = {
        '_id': ObjectId(),
        'lemma': ['lemma'],
        'homonym': 'I'
    }

    with pytest.raises(KeyError):
        dictionary.update(word)

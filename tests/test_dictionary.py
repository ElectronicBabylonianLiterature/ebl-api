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

    assert dictionary.search(lemma) == [word1, word2]

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

    assert dictionary.search(lemma) == [word1, word2]

def test_search_not_found(dictionary):
    assert dictionary.search(['lemma']) == []

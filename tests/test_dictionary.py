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

    assert dictionary.find(lemma, homonym) == expected_word

def test_word_not_found(dictionary):
    lemma = ['part1', 'part2']
    homonym = 'I'
    with pytest.raises(KeyError):
        dictionary.find(lemma, homonym)

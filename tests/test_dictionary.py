from bson.objectid import ObjectId
import pytest


def test_create_and_find(mongo_dictionary):
    lemma = ['part1', 'part2']
    homonym = 'I'

    word = {
        'lemma': lemma,
        'homonym': homonym
    }

    word_id = mongo_dictionary.create(word)

    expected_word = {
        '_id': word_id,
        'lemma': lemma,
        'homonym': homonym
    }

    assert mongo_dictionary.find(word_id) == expected_word


def test_word_not_found(mongo_dictionary):
    with pytest.raises(KeyError):
        mongo_dictionary.find(ObjectId())


def test_search_finds_all_homonyms(mongo_dictionary):
    lemma = ['part1', 'part2']

    word1 = {
        'lemma': lemma,
        'homonym': 'I'
    }
    mongo_dictionary.create(word1)

    word2 = {
        'lemma': lemma,
        'homonym': 'II'
    }
    mongo_dictionary.create(word2)

    assert mongo_dictionary.search(' '.join(lemma)) == [word1, word2]


def test_search_finds_by_meaning(mongo_dictionary):
    word1 = {
        'lemma': ['lemma'],
        'meaning': 'meaning',
        'homonym': 'I'
    }
    mongo_dictionary.create(word1)

    word2 = {
        'lemma': ['lemma'],
        'meaning': 'not matching',
        'homonym': 'II'
    }
    mongo_dictionary.create(word2)

    assert mongo_dictionary.search(word1['meaning'][1:4]) == [word1]


def test_search_finds_duplicates(mongo_dictionary):
    lemma = ['part1', 'part2']
    homonym = 'I'

    word1 = {
        'lemma': lemma,
        'homonym': homonym
    }
    mongo_dictionary.create(word1)

    word2 = {
        'lemma': lemma,
        'homonym': homonym
    }
    mongo_dictionary.create(word2)

    assert mongo_dictionary.search(' '.join(lemma)) == [word1, word2]


def test_search_not_found(mongo_dictionary):
    assert mongo_dictionary.search('lemma') == []


def test_update(mongo_dictionary):
    lemma = ['part1', 'part2']
    new_lemma = ['new']
    homonym = 'I'

    word = {
        'lemma': lemma,
        'homonym': homonym
    }

    word_id = mongo_dictionary.create(word)

    updated_word = {
        '_id': word_id,
        'lemma': new_lemma,
        'homonym': homonym
    }

    mongo_dictionary.update(updated_word)

    assert mongo_dictionary.find(word_id) == updated_word


def test_update_word_not_found(mongo_dictionary):
    word = {
        '_id': ObjectId(),
        'lemma': ['lemma'],
        'homonym': 'I'
    }

    with pytest.raises(KeyError):
        mongo_dictionary.update(word)

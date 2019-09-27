import pydash
import pytest

from ebl.errors import NotFoundError

COLLECTION = 'words'


def test_create(database, word_repository, word):
    word_id = word_repository.create(word)

    assert database[COLLECTION].find_one({'_id': word_id}) == word


def test_find(database, word_repository, word):
    database[COLLECTION].insert_one(word)

    assert word_repository.query_by_id(word['_id']) == word


def test_word_not_found(word_repository):
    with pytest.raises(NotFoundError):
        word_repository.query_by_id('not found')


def test_search_finds_all_homonyms(database, word_repository, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_form_or_meaning(
        ' '.join(word['lemma'])
    ) == [word, another_word]


def test_search_finds_by_meaning(database, word_repository, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II',
        'meaning': 'not matching'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_form_or_meaning(
        word['meaning'][1:4]
    ) == [word]


def test_search_finds_duplicates(database, word_repository, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    database[COLLECTION].insert_many([word, another_word])

    assert word_repository.query_by_lemma_form_or_meaning(
        word['meaning'][1:4]
    ) == [word, another_word]


def test_search_not_found(word_repository):
    assert word_repository.query_by_lemma_form_or_meaning('lemma') == []


def test_update(word_repository, word):
    new_lemma = ['new']
    word_id = word_repository.create(word)
    updated_word = pydash.defaults({'lemma': new_lemma}, word)

    word_repository.update(updated_word)

    assert word_repository.query_by_id(word_id) == updated_word

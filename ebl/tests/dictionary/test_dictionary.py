import pydash
import pytest
from freezegun import freeze_time

from ebl.errors import NotFoundError

COLLECTION = 'words'


def test_create_and_find(database, dictionary, word):
    word_id = dictionary.create(word)

    assert dictionary.find(word_id) == word


def test_word_not_found(dictionary):
    with pytest.raises(NotFoundError):
        dictionary.find('not found')


def test_search_finds_all_homonyms(dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    dictionary.create(word)
    dictionary.create(another_word)

    assert dictionary.search(' '.join(word['lemma'])) == [word, another_word]


def test_search_finds_by_meaning(dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II',
        'meaning': 'not matching'
    }
    dictionary.create(word)
    dictionary.create(another_word)

    assert dictionary.search(word['meaning'][1:4]) == [word]


def test_search_finds_duplicates(dictionary, word):
    another_word = {
        **word,
        '_id': 'part1 part2 II',
        'homonym': 'II'
    }
    dictionary.create(word)
    dictionary.create(another_word)

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
    with pytest.raises(NotFoundError):
        dictionary.update(pydash.defaults({'_id': 'not found'}, word), user)

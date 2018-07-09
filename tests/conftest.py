# pylint: disable=W0621
import pytest
import mongomock

from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragmentarium.fragmentarium import MongoFragmentarium


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def dictionary(database):
    return MongoDictionary(database)


@pytest.fixture
def fragmentarium(database):
    return MongoFragmentarium(database)


@pytest.fixture
def word():
    return {
        'lemma': ['part1', 'part2'],
        'homonym': 'I',
        'meaning': 'a meaning'
    }


@pytest.fixture
def fragment():
    return {
        '_id': '1',
        'transliteration': ''
    }

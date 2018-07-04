import pytest
import mongomock

from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragmentarium.fragmentarium import MongoFragmentarium


@pytest.fixture
def dictionary():
    return MongoDictionary(mongomock.MongoClient().ebl)


@pytest.fixture
def fragmentarium():
    return MongoFragmentarium(mongomock.MongoClient().ebl)


@pytest.fixture
def fragment():
    return {'_id': '1'}

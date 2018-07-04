import pytest
import mongomock

from ebl.dictionary.dictionary import MongoDictionary


@pytest.fixture
def mongo_dictionary():
    return MongoDictionary(mongomock.MongoClient().dictionary)

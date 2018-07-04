# pylint: disable=W0621
import pytest
import mongomock

from ebl.fragmentarium.fragmentarium import MongoFragmentarium


@pytest.fixture
def fragmentarium():
    return MongoFragmentarium(mongomock.MongoClient().fragmentarium)


def test_create_and_find(fragmentarium):
    fragment = {
        '_id': '1'
    }

    fragmentarium.create(fragment)

    assert fragmentarium.find(fragment['_id']) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')

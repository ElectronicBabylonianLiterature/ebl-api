import pytest


def test_create_and_find(fragmentarium, fragment):
    fragmentarium.create(fragment)

    assert fragmentarium.find(fragment['_id']) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')

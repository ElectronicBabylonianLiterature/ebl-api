import pydash
import pytest


def test_create_and_find(fragmentarium, fragment):
    fragmentarium.create(fragment)

    assert fragmentarium.find(fragment['_id']) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')


def test_update_transliteration(fragmentarium, fragment):
    fragmentarium.create(fragment)
    transliteration = 'the transliteration'

    fragmentarium.update_transliteration(fragment['_id'], transliteration)
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.assign(
        {},
        fragment,
        {'transliteration': transliteration}
    )

    assert updated_fragment == expected_fragment

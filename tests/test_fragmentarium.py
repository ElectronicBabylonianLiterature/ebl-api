import datetime
from freezegun import freeze_time
import pydash
import pytest

COLLECTION = 'fragments'
USER = 'user@example.com'


def test_create(database, fragmentarium, fragment):
    fragment_id = fragmentarium.create(fragment)

    assert database[COLLECTION].find_one({'_id': fragment_id}) == fragment


def test_find(database, fragmentarium, fragment):
    database[COLLECTION].insert_one(fragment)

    assert fragmentarium.find(fragment['_id']) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragmentarium, fragment):
    fragmentarium.create(fragment)
    transliteration = 'the transliteration'

    fragmentarium.update_transliteration(
        fragment['_id'],
        transliteration,
        USER
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': transliteration,
            'record': [{
                'user': USER,
                'type': 'Transliteration',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragmentarium, fragment):
    fragmentarium.create(pydash.defaults({
        'transliteration': 'old transliteration'
    }, fragment))
    updated_transliteration = 'the updated transliteration'

    fragmentarium.update_transliteration(
        fragment['_id'],
        updated_transliteration,
        USER
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updated_transliteration,
            'record': [{
                'user': USER,
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


def test_update_update_transliteration_not_found(fragmentarium):
    # pylint: disable=C0103
    with pytest.raises(KeyError):
        fragmentarium.update_transliteration(
            'unknown.number',
            'transliteration',
            USER
        )

# pylint: disable=W0621
import pytest

from ebl.fragmentarium.sign_list import SignList


COLLECTION = 'signs'


@pytest.fixture
def sign_list(database):
    return SignList(database)


@pytest.fixture
def sign():
    return {
        '_id': 'IGI',
        'lists': [
            'HZL288'
        ],
        'unicode': [
            74054
        ],
        'notes': [],
        'internalNotes': [],
        'literature': [],
        'values': [
            {
                'value': 'ši',
                'subIndex': 1,
                'questionable': False,
                'deprecated': False,
                'notes': [],
                'internalNotes': []
            },
            {
                'value': 'panu',
                'subIndex': 1,
                'questionable': False,
                'deprecated': False,
                'languageRestriction': 'akk',
                'notes': [],
                'internalNotes': []
            }
        ],
        'forms': []
    }


@pytest.fixture
def another_sign():
    return {
        '_id': 'SI',
        'lists': [],
        'unicode': [],
        'notes': [],
        'internalNotes': [],
        'literature': [],
        'values': [
            {
                'value': 'ši',
                'subIndex': 2,
                'questionable': False,
                'deprecated': False,
                'notes': [],
                'internalNotes': []
            },
            {
                'value': 'hu',
                'questionable': False,
                'deprecated': False,
                'notes': [],
                'internalNotes': []
            },
        ],
        'forms': []
    }


def test_create(database, sign_list, sign):
    sign_name = sign_list.create(sign)

    assert database[COLLECTION].find_one({'_id': sign_name}) == sign


def test_find(database, sign_list, sign):
    database[COLLECTION].insert_one(sign)

    assert sign_list.find(sign['_id']) == sign


def test_fragment_not_found(sign_list):
    with pytest.raises(KeyError):
        sign_list.find('unknown id')


def test_search(database,
                sign_list,
                sign,
                another_sign):
    database[COLLECTION].insert_many([sign, another_sign])

    assert sign_list.search('ši', 1) == sign
    assert sign_list.search('hu', None) == another_sign


def test_search_not_found(sign_list):
    assert sign_list.search('unknown', 1) is None

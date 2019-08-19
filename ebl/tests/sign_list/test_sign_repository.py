import pytest

from ebl.errors import NotFoundError

COLLECTION = 'signs'


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


def test_create(database, sign_repository, sign):
    sign_name = sign_repository.create(sign)

    assert database[COLLECTION].find_one({'_id': sign_name}) == sign


def test_find(database, sign_repository, sign):
    database[COLLECTION].insert_one(sign)

    assert sign_repository.find(sign['_id']) == sign


def test_sign_not_found(sign_repository):
    with pytest.raises(NotFoundError):
        sign_repository.find('unknown id')


def test_search(database,
                sign_repository,
                sign,
                another_sign):
    database[COLLECTION].insert_many([sign, another_sign])

    assert sign_repository.search('ši', 1) == sign
    assert sign_repository.search('hu', None) == another_sign


def test_search_not_found(sign_repository):
    assert sign_repository.search('unknown', 1) is None


def test_search_many_one_reading(sign_repository, sign, another_sign):
    sign_repository.create(sign)
    sign_repository.create(another_sign)
    value: dict = sign['values'][0]

    assert sign_repository.search_many([
        (value['value'], value['subIndex'])
    ]) == [sign]


def test_search_many_multiple_readings(sign_repository, sign, another_sign):
    sign_repository.create(sign)
    sign_repository.create(another_sign)
    first_value: dict = sign['values'][0]
    second_value: dict = another_sign['values'][0]
    assert sign_repository.search_many([
        (first_value['value'], first_value['subIndex']),
        (second_value['value'], second_value['subIndex'])
    ]) == [sign, another_sign]


def test_search_many_no_readings(sign_repository, sign, another_sign):
    sign_repository.create(sign)
    sign_repository.create(another_sign)

    assert sign_repository.search_many([]) == []

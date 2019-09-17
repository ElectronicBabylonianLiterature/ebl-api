import pytest

from ebl.errors import NotFoundError
from ebl.sign_list.sign import Sign, SignListRecord, Value
from ebl.sign_list.sign_repository import SignSchema

COLLECTION = 'signs'


@pytest.fixture
def mongo_sign():
    return {
        '_id': 'IGI',
        'lists': [
            {
                'name': 'HZL',
                'number': '288'
            }
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
def sign(mongo_sign):
    return Sign(mongo_sign['_id'],
                tuple(map(lambda data: SignListRecord(**data),
                          mongo_sign['lists'])),
                tuple(map(lambda data: Value(data['value'], data['subIndex']),
                          mongo_sign['values'])))


@pytest.fixture
def another_mongo_sign():
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


@pytest.fixture
def another_sign(another_mongo_sign):
    return Sign(
        another_mongo_sign['_id'],
        tuple(map(lambda data: SignListRecord(**data),
                  another_mongo_sign['lists'])),
        tuple(map(lambda data: Value(data['value'], data.get('subIndex')),
                  another_mongo_sign['values']))
    )


def test_load():
    data = {
        '_id': 'KUR',
        'lists': [
            {'name': 'ABZ', 'number': '03+53'}
        ],
        'values': [
            {'value': 'kur', 'subIndex': 3},
            {'value': 'ruk'},
        ]
    }
    sign = Sign('KUR',
                (SignListRecord('ABZ', '03+53'),),
                (Value('kur', 3), Value('ruk')))
    assert SignSchema().load(data) == sign


def test_dump():
    sign = Sign('KUR',
                (SignListRecord('ABZ', '03+53'), ),
                (Value('kur', 3), Value('ruk')))
    data = {
        '_id': 'KUR',
        'lists': [
            {'name': 'ABZ', 'number': '03+53'}
        ],
        'values': [
            {'value': 'kur', 'subIndex': 3},
            {'value': 'ruk'},
        ]
    }
    assert SignSchema().dump(sign) == data


def test_create(database, sign_repository, sign):
    sign_name = sign_repository.create(sign)

    assert database[COLLECTION].find_one({'_id': sign_name}) ==\
        SignSchema().dump(sign)


def test_find(database, sign_repository, sign, mongo_sign):
    database[COLLECTION].insert_one(mongo_sign)

    assert sign_repository.find(mongo_sign['_id']) == sign


def test_sign_not_found(sign_repository):
    with pytest.raises(NotFoundError):
        sign_repository.find('unknown id')


def test_search(database,
                sign_repository,
                sign,
                mongo_sign,
                another_sign,
                another_mongo_sign):
    database[COLLECTION].insert_many([mongo_sign, another_mongo_sign])

    assert sign_repository.search('ši', 1) == sign
    assert sign_repository.search('hu', None) == another_sign


def test_search_not_found(sign_repository):
    assert sign_repository.search('unknown', 1) is None


def test_search_many_one_reading(sign_repository, sign, another_sign):
    sign_repository.create(sign)
    sign_repository.create(another_sign)
    value = sign.values[0]

    assert sign_repository.search_many([
        (value.value, value.sub_index)
    ]) == [sign]


def test_search_many_multiple_readings(sign_repository, sign, another_sign):
    sign_repository.create(sign)
    sign_repository.create(another_sign)
    first_value = sign.values[0]
    second_value = another_sign.values[0]
    assert sign_repository.search_many([
        (first_value.value, first_value.sub_index),
        (second_value.value, second_value.sub_index)
    ]) == [sign, another_sign]


def test_search_many_no_readings(sign_repository, mongo_sign,
                                 another_mongo_sign):
    sign_repository.create(mongo_sign)
    sign_repository.create(another_mongo_sign)

    assert sign_repository.search_many([]) == []

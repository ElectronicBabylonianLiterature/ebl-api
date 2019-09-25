import pytest

from ebl.errors import NotFoundError
from ebl.transliteration_search.domain.sign import Sign, SignListRecord, \
    SignName, Value
from ebl.transliteration_search.infrastructure.mongo_sign_repository import \
    SignSchema

COLLECTION = 'signs'


@pytest.fixture
def mongo_sign_igi():
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
def sign_igi(mongo_sign_igi):
    return Sign(mongo_sign_igi['_id'],
                tuple(map(lambda data: SignListRecord(**data),
                          mongo_sign_igi['lists'])),
                tuple(map(lambda data: Value(data['value'], data['subIndex']),
                          mongo_sign_igi['values'])))


@pytest.fixture
def mongo_sign_si():
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
def sign_si(mongo_sign_si):
    return Sign(
        mongo_sign_si['_id'],
        tuple(map(lambda data: SignListRecord(**data),
                  mongo_sign_si['lists'])),
        tuple(map(lambda data: Value(data['value'], data.get('subIndex')),
                  mongo_sign_si['values']))
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
    sign = Sign(SignName('KUR'),
                (SignListRecord('ABZ', '03+53'),),
                (Value('kur', 3), Value('ruk')))
    assert SignSchema().load(data) == sign


def test_dump():
    sign = Sign(SignName('KUR'),
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


def test_create(database, sign_repository, sign_igi):
    sign_name = sign_repository.create(sign_igi)

    assert database[COLLECTION].find_one({'_id': sign_name}) ==\
        SignSchema().dump(sign_igi)


def test_find(database, sign_repository, sign_igi, mongo_sign_igi):
    database[COLLECTION].insert_one(mongo_sign_igi)

    assert sign_repository.find(mongo_sign_igi['_id']) == sign_igi


def test_sign_not_found(sign_repository):
    with pytest.raises(NotFoundError):
        sign_repository.find('unknown id')


def test_search(database,
                sign_repository,
                sign_igi,
                mongo_sign_igi,
                sign_si,
                mongo_sign_si):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si])

    assert sign_repository.search('ši', 1) == sign_igi
    assert sign_repository.search('hu', None) == sign_si


def test_search_not_found(sign_repository):
    assert sign_repository.search('unknown', 1) is None


def test_search_many_one_reading(sign_repository, sign_igi, sign_si):
    sign_repository.create(sign_igi)
    sign_repository.create(sign_si)
    value = sign_igi.values[0]

    assert sign_repository.search_many([value]) == [sign_igi]


def test_search_many_multiple_readings(sign_repository, sign_igi, sign_si):
    sign_repository.create(sign_igi)
    sign_repository.create(sign_si)
    first_value = sign_igi.values[0]
    second_value = sign_si.values[0]
    assert sign_repository.search_many([
        first_value,
        second_value
    ]) == [sign_igi, sign_si]


def test_search_many_no_readings(sign_repository, mongo_sign_igi,
                                 mongo_sign_si):
    sign_repository.create(mongo_sign_igi)
    sign_repository.create(mongo_sign_si)

    assert sign_repository.search_many([]) == []

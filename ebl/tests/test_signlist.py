# pylint: disable=W0621
import pytest


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
    # pylint: disable=R0801
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


def test_sign_not_found(sign_list):
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


def test_transliteration_to_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    clean_transliteration = [
        'šu gid₂',
        'BI IS',
        'BIxIS',
        '|BIxIS|',
        'unknown x',
        '1(AŠ) 1 2 10 20 30 256',
        'foo(TUKUL)',
        'šu/gid₂'
    ]
    mapped_signs = sign_list.map_transliteration(clean_transliteration)

    assert mapped_signs == [
        ['ŠU', 'BU'],
        ['BI', 'IS'],
        ['BIxIS'],
        ['|BIxIS|'],
        ['X', 'X'],
        # 1, 2, 10, 20, 30 should be inserted manually to the sign list
        ['AŠ', '1', '2', '10', '20', '30', '256'],
        ['TUKUL'],
        ['ŠU/BU']
    ]

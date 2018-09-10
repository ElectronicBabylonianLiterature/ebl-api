# pylint: disable=W0621
import pytest

from ebl.fragmentarium.transliteration_to_signs import transliteration_to_signs


@pytest.fixture
def signs():
    return [{
        '_id': 'ŠU',
        'lists': [],
        'unicode': [
            74455
        ],
        'notes': [],
        'internalNotes': [],
        'literature': [],
        'values': [
            {
                'value': 'šu',
                'subIndex': 1,
                'questionable': False,
                'deprecated': False,
                'notes': [],
                'internalNotes': []
            }
        ],
        'forms': []
    }, {
        '_id': 'BU',
        'lists': [],
        'unicode': [
            73805
        ],
        'notes': [],
        'internalNotes': [],
        'literature': [],
        'values': [
            {
                'value': 'gid',
                'subIndex': 2,
                'questionable': False,
                'deprecated': False,
                'notes': [],
                'internalNotes': []
            },
        ],
        'forms': []
    }]


def test_transliteration_to_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    clean_transliteration = [
        'šu gid₂',
        'BI IS',
        'BIxIS',
        '|BIxIS|',
        'unknown x'
    ]
    mapped_signs = transliteration_to_signs(clean_transliteration, sign_list)

    assert mapped_signs == [
        ['ŠU', 'BU'],
        ['BI', 'IS'],
        ['BIxIS'],
        ['|BIxIS|'],
        ['X', 'X']
    ]

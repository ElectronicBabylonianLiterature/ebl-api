import datetime
from freezegun import freeze_time
from ebl.fragmentarium.fragment import Fragment


def test_to_dict(fragment):
    new_fragment = Fragment(fragment.to_dict())

    assert new_fragment.to_dict() == fragment.to_dict()


def test_equality(fragment, transliterated_fragment):
    new_fragment = Fragment(fragment.to_dict())

    assert new_fragment == fragment
    assert new_fragment != transliterated_fragment


def test_accession(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.accession == data['accession']


def test_cdli_number(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.cdli_number == data['cdliNumber']


def test_transliteration(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.transliteration == data['transliteration']


def test_notes(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.notes == data['notes']


def test_signs(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.signs == data['signs']


def signs_not_set(fragment):
    assert fragment.signs is None


def test_record(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment(data)

    assert new_fragment.record == data['record']


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
    transliteration = 'x x'

    updated_fragment = fragment.update_transliteration(
        transliteration,
        fragment.notes,
        user
    )
    expected_fragment = Fragment({
        **fragment.to_dict(),
        'transliteration': transliteration,
        'record': [{
            'user': user.ebl_name,
            'type': 'Transliteration',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    })

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(transliterated_fragment, user):
    transliteration = '1. x x\n2. x'
    notes = 'updated notes'

    updated_fragment = transliterated_fragment.update_transliteration(
        transliteration,
        notes,
        user
    )

    expected_fragment = Fragment({
        **transliterated_fragment.to_dict(),
        'transliteration': transliteration,
        'notes': notes,
        'record': [
            *transliterated_fragment.to_dict()['record'],
            {
                'user': user.ebl_name,
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }
        ]
    })

    assert updated_fragment == expected_fragment


def test_update_notes(fragment, user):
    notes = 'new notes'

    updated_fragment = fragment.update_transliteration(
        fragment.transliteration,
        notes,
        user
    )

    expected_fragment = Fragment({
        **fragment.to_dict(),
        'notes': notes
    })

    assert updated_fragment == expected_fragment


def test_set_signs(fragment):
    signs = ['X']

    updated_fragment = fragment.set_signs(signs)

    expected_fragment = Fragment({
        **fragment.to_dict(),
        'signs': signs
    })

    assert updated_fragment == expected_fragment

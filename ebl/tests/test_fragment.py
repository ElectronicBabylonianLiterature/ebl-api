import datetime
from freezegun import freeze_time
from ebl.fragmentarium.fragment import Fragment


def test_to_dict(fragment):
    fragment_model = Fragment(fragment)

    assert fragment_model.to_dict() == fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
    fragment_model = Fragment(fragment)
    transliteration = 'x x'

    updated_fragment = fragment_model.update_transliteration(
        transliteration,
        fragment['notes'],
        user
    )
    expected_fragment = {
        **fragment,
        'transliteration': transliteration,
        'record': [{
            'user': user.ebl_name,
            'type': 'Transliteration',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    }

    assert updated_fragment.to_dict() == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragment, user):
    fragment_model = Fragment({
        **fragment,
        'transliteration': '1. x x'
    })
    transliteration = '1. x x\n2. x'
    notes = 'updated notes'

    updated_fragment = fragment_model.update_transliteration(
        transliteration,
        notes,
        user
    )

    expected_fragment = {
        **fragment,
        'transliteration': transliteration,
        'notes': notes,
        'record': [{
            'user': user.ebl_name,
            'type': 'Revision',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    }

    assert updated_fragment.to_dict() == expected_fragment


def test_update_notes(fragment, user):
    fragment_model = Fragment(fragment)
    notes = 'new notes'

    updated_fragment = fragment_model.update_transliteration(
        fragment['transliteration'],
        notes,
        user
    )

    expected_fragment = {
        **fragment,
        'notes':notes
    }

    assert updated_fragment.to_dict() == expected_fragment

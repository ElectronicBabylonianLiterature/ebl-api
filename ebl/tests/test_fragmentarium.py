# pylint: disable=W0621
import datetime
from freezegun import freeze_time
import pydash
import pytest


COLLECTION = 'fragments'


@pytest.fixture
def another_fragment(fragment):
    return pydash.defaults({
        '_id': '2',
        'accession': 'accession-no-match',
        'cdliNumber': 'cdli-no-match'
    }, fragment)


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
def test_add_transliteration(fragmentarium, fragment, user):
    fragmentarium.create(fragment)
    updates = {
        'transliteration': 'x x',
        'notes': fragment['notes']
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updates['transliteration'],
            'signs': 'X X',
            'notes': fragment['notes'],
            'record': [{
                'user': user.ebl_name,
                'type': 'Transliteration',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragmentarium, fragment, user):
    fragmentarium.create(pydash.defaults({
        'transliteration': '1. x x'
    }, fragment))
    updates = {
        'transliteration': '1. x x\n2. x',
        'notes': 'updated notes'
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updates['transliteration'],
            'signs': 'X X\nX',
            'notes': updates['notes'],
            'record': [{
                'user': user.ebl_name,
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


def test_update_notes(fragmentarium, fragment, user):
    fragmentarium.create(fragment)
    updates = {
        'transliteration': fragment['transliteration'],
        'notes': 'new nites'
    }

    fragmentarium.update_transliteration(
        fragment['_id'],
        updates,
        user
    )
    updated_fragment = fragmentarium.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'notes': updates['notes'],
            'signs': '',
            'record': []
        },
        fragment
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(database,
                   fragmentarium,
                   fragment,
                   user,
                   make_changelog_entry):
    fragment_id = fragmentarium.create(fragment)
    updates = {
        'transliteration':  'x x x',
        'notes': 'updated notes'
    }

    fragmentarium.update_transliteration(
        fragment_id,
        updates,
        user
    )

    expected_changelog = make_changelog_entry(
        COLLECTION,
        fragment_id,
        pydash.pick(fragment, 'transliteration', 'notes', 'signs'),
        pydash.defaults(updates, {'signs': 'X X X'})
    )
    assert database['changelog'].find_one(
        {'resource_id': fragment_id},
        {'_id': 0}
    ) == expected_changelog


def test_update_update_transliteration_not_found(fragmentarium, user):
    # pylint: disable=C0103
    with pytest.raises(KeyError):
        fragmentarium.update_transliteration(
            'unknown.number',
            {'transliteration': 'transliteration'},
            user
        )


def test_statistics(database, fragmentarium, fragment):
    database[COLLECTION].insert_many([
        pydash.defaults({'_id': '1', 'transliteration': '''1. first line
$ingore

'''}, fragment),
        pydash.defaults({'_id': '2', 'transliteration': '''@ignore
1'. second line
2'. third line
@ignore
1#. fourth line'''}, fragment),
        pydash.defaults({'_id': '3', 'transliteration': ''}, fragment),
    ])

    assert fragmentarium.statistics() == {
        'transliteratedFragments': 2,
        'lines': 4
    }


def test_statistics_no_fragments(fragmentarium):
    assert fragmentarium.statistics() == {
        'transliteratedFragments': 0,
        'lines': 0
    }


def test_search_finds_by_id(database,
                            fragmentarium,
                            fragment,
                            another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['_id']) == [fragment]


def test_search_finds_by_accession(database,
                                   fragmentarium,
                                   fragment,
                                   another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['accession']) == [fragment]


def test_search_finds_by_cdli(database,
                              fragmentarium,
                              fragment,
                              another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragmentarium.search(fragment['cdliNumber']) == [fragment]


def test_search_not_found(fragmentarium):
    assert fragmentarium.search('K.1') == []


SEARCH_TRANSLITERATION_DATA = [
    ('ana u₄', [
        ['2\'. [...] GI₆ ana u₄-š[u ...]']
    ]),
    ('ku', [
        ['1\'. [...-ku]-nu-ši [...]']
    ]),
    ('u₄', [
        ['2\'. [...] GI₆ ana u₄-š[u ...]'],
        ['6\'. [...] x mu ta-ma-tu₂']
    ]),
    ('GI₆ ana\nu ba ma', [
        [
            '2\'. [...] GI₆ ana u₄-š[u ...]',
            '3\'. [... k]i-du u ba-ma-t[i ...]'
        ]
    ]),
    ('ši tu₂', None),
]


@pytest.mark.parametrize("transliteration,lines", SEARCH_TRANSLITERATION_DATA)
def test_search_signs(transliteration,
                      lines,
                      sign_list,
                      signs,
                      fragmentarium,
                      transliterated_fragment,
                      another_fragment):
    # pylint: disable=R0913
    fragmentarium.create(transliterated_fragment)
    fragmentarium.create(another_fragment)
    for sign in signs:
        sign_list.create(sign)

    result = fragmentarium.search_signs(transliteration)
    expected = [(transliterated_fragment, lines)] if lines else []

    assert result == expected

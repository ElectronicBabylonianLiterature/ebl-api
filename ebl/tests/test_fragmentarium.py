from freezegun import freeze_time
import pytest
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.transliterations import Transliteration


def test_create_and_find(fragmentarium, fragment):
    fragment_id = fragmentarium.create(fragment)

    assert fragmentarium.find(fragment_id) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(KeyError):
        fragmentarium.find('unknown id')


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragmentarium, transliterated_fragment, user):
    fragment_number = fragmentarium.create(transliterated_fragment)

    fragmentarium.update_transliteration(
        fragment_number,
        Transliteration('1. x x\n2. x', 'updated notes'),
        user
    )
    updated_fragment = fragmentarium.find(fragment_number)

    expected_fragment = transliterated_fragment.update_transliteration(
        Transliteration('1. x x\n2. x', 'updated notes', 'X X\nX'),
        user
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(database,
                   fragmentarium,
                   fragment,
                   user,
                   make_changelog_entry):
    fragment_id = fragmentarium.create(fragment)
    fragmentarium.update_transliteration(
        fragment_id,
        Transliteration('x x x', 'updated notes'),
        user
    )

    expected_fragment = fragment.update_transliteration(
        Transliteration('x x x', 'updated notes', 'X X X'),
        user
    )

    expected_changelog = make_changelog_entry(
        'fragments',
        fragment_id,
        fragment.to_dict(),
        expected_fragment.to_dict()
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
            Transliteration('transliteration', 'notes'),
            user
        )


def test_statistics(fragmentarium, fragment):
    for data in [
            {**fragment.to_dict(), '_id': '1', 'transliteration': '''1. first line
$ingore

'''},
            {**fragment.to_dict(), '_id': '2', 'transliteration': '''@ignore
1'. second line
2'. third line
@ignore
1#. fourth line'''},
            {**fragment.to_dict(), '_id': '3', 'transliteration': ''},
    ]:
        fragmentarium.create(Fragment(data))

    assert fragmentarium.statistics() == {
        'transliteratedFragments': 2,
        'lines': 4
    }


def test_statistics_no_fragments(fragmentarium):
    assert fragmentarium.statistics() == {
        'transliteratedFragments': 0,
        'lines': 0
    }


def test_search_finds_by_id(fragmentarium,
                            fragment,
                            another_fragment):
    fragmentarium.create(fragment)
    fragmentarium.create(another_fragment)

    assert fragmentarium.search(fragment.number) == [fragment]


def test_search_finds_by_accession(fragmentarium,
                                   fragment,
                                   another_fragment):
    fragmentarium.create(fragment)
    fragmentarium.create(another_fragment)

    assert fragmentarium.search(fragment.accession) == [fragment]


def test_search_finds_by_cdli(fragmentarium,
                              fragment,
                              another_fragment):
    fragmentarium.create(fragment)
    fragmentarium.create(another_fragment)

    assert fragmentarium.search(fragment.cdli_number) == [fragment]


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

    result = fragmentarium.search_signs(
        Transliteration(transliteration)
    )
    expected = [
        Fragment({
            **transliterated_fragment.to_dict(),
            'matching_lines': lines
        })
    ] if lines else []

    assert result == expected

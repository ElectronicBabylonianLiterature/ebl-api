from freezegun import freeze_time
import pytest
from ebl.errors import NotFoundError
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.lemmatization import Lemmatization
from ebl.fragmentarium.transliteration import (
    Transliteration, TransliterationError
)


def test_create_and_find(fragmentarium, fragment):
    fragment_id = fragmentarium.create(fragment)

    assert fragmentarium.find(fragment_id) == fragment


def test_fragment_not_found(fragmentarium):
    with pytest.raises(NotFoundError):
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


def test_update_transliteration_invalid(fragmentarium, fragment, user):
    fragment_number = fragmentarium.create(fragment)

    with pytest.raises(TransliterationError):
        fragmentarium.update_transliteration(
            fragment_number,
            Transliteration('1. invalid values'),
            user
        )


@freeze_time("2018-09-07 15:41:24.032")
def test_transliteration_changelog(database,
                                   fragmentarium,
                                   fragment,
                                   user,
                                   make_changelog_entry):
    fragment_id = fragmentarium.create(fragment)
    fragmentarium.update_transliteration(
        fragment_id,
        Transliteration('1. x x x', 'updated notes'),
        user
    )

    expected_fragment = fragment.update_transliteration(
        Transliteration('1. x x x', 'updated notes', 'X X X'),
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
    with pytest.raises(NotFoundError):
        fragmentarium.update_transliteration(
            'unknown.number',
            Transliteration('$ (the transliteration)', 'notes'),
            user
        )


@freeze_time("2018-09-07 15:41:24.032")
def test_lemmatization_transliteration(fragmentarium,
                                       transliterated_fragment,
                                       user):
    fragment_number = fragmentarium.create(transliterated_fragment)
    tokens = transliterated_fragment.lemmatization.tokens
    tokens[0][1]['uniqueLemma'] = ['aklu I']
    lemmatization = Lemmatization(tokens)

    fragmentarium.update_lemmatization(
        fragment_number,
        lemmatization,
        user
    )
    updated_fragment = fragmentarium.find(fragment_number)

    expected_fragment = transliterated_fragment.update_lemmatization(
        lemmatization
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_lemmatization_changelog(database,
                                 fragmentarium,
                                 transliterated_fragment,
                                 user,
                                 make_changelog_entry):
    fragment_number = fragmentarium.create(transliterated_fragment)
    tokens = transliterated_fragment.lemmatization.tokens
    tokens[0][1]['uniqueLemma'] = ['aklu I']
    lemmatization = Lemmatization(tokens)
    fragmentarium.update_lemmatization(
        fragment_number,
        lemmatization,
        user
    )

    expected_fragment = transliterated_fragment.update_lemmatization(
        lemmatization
    )

    expected_changelog = make_changelog_entry(
        'fragments',
        fragment_number,
        transliterated_fragment.to_dict(),
        expected_fragment.to_dict()
    )
    assert database['changelog'].find_one(
        {'resource_id': fragment_number},
        {'_id': 0}
    ) == expected_changelog


def test_update_update_lemmatization_not_found(fragmentarium, user):
    with pytest.raises(NotFoundError):
        fragmentarium.update_lemmatization(
            'K.1',
            Lemmatization([[{'value': '1.', 'uniqueLemma': []}]]),
            user
        )


def test_statistics(fragmentarium, fragment):
    for data in [
            {**fragment.to_dict(), '_id': '1', 'lemmatization': [
                [{'value': '1. SU', 'uniqueLemma': []}],
                [{'value': '$ingore', 'uniqueLemma': []}],
                [],
                [{'value': '', 'uniqueLemma': []}]
            ]},
            {**fragment.to_dict(), '_id': '2', 'lemmatization': [
                [{'value': '$ingore', 'uniqueLemma': []}],
                [{'value': '1. SU', 'uniqueLemma': []}],
                [{'value': '2. SU', 'uniqueLemma': []}],
                [{'value': '$ingore', 'uniqueLemma': []}],
                [{'value': '1#. SU', 'uniqueLemma': []}]
            ]},
            {**fragment.to_dict(), '_id': '3', 'lemmatization': []}
    ]:
        fragmentarium.create(Fragment.from_dict(data))

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
        Fragment.from_dict({
            **transliterated_fragment.to_dict(),
            'matching_lines': lines
        })
    ] if lines else []

    assert result == expected

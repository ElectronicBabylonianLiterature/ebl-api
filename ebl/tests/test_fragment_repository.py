# pylint: disable=W0621
import datetime
import pydash
import pytest
from ebl.fragmentarium.transliteration_query import TransliterationQuery


COLLECTION = 'fragments'


@pytest.fixture
def another_fragment(fragment):
    return pydash.defaults({
        '_id': '2',
        'accession': 'accession-no-match',
        'cdliNumber': 'cdli-no-match'
    }, fragment)


def test_create(database, fragment_repository, fragment):
    fragment_id = fragment_repository.create(fragment)

    assert database[COLLECTION].find_one({'_id': fragment_id}) == fragment


def test_find(database, fragment_repository, fragment):
    database[COLLECTION].insert_one(fragment)

    assert fragment_repository.find(fragment['_id']) == fragment


def test_fragment_not_found(fragment_repository):
    with pytest.raises(KeyError):
        fragment_repository.find('unknown id')


def test_update_transliteration_with_record(fragment_repository, fragment):
    fragment_repository.create(fragment)
    updates = {
        'transliteration': 'the transliteration',
        'notes': fragment['notes']
    }
    record = {
        'user': 'Tester',
        'type': 'Transliteration',
        'date': datetime.datetime.utcnow().isoformat()
    }

    fragment_repository.update_transliteration(
        fragment['_id'],
        updates,
        record
    )
    updated_fragment = fragment_repository.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'transliteration': updates['transliteration'],
            'notes': fragment['notes'],
            'record': [record]
        },
        fragment
    )

    assert updated_fragment == expected_fragment


def test_update_transliteration_without_record(fragment_repository, fragment):
    fragment_repository.create(pydash.defaults({
        'transliteration': 'old transliteration'
    }, fragment))
    updates = {
        'transliteration':  fragment['transliteration'],
        'notes': 'updated notes'
    }

    fragment_repository.update_transliteration(
        fragment['_id'],
        updates,
        None
    )
    updated_fragment = fragment_repository.find(fragment['_id'])

    expected_fragment = pydash.defaults(
        {
            'notes': updates['notes'],
        },
        fragment
    )

    assert updated_fragment == expected_fragment


def test_update_update_transliteration_not_found(fragment_repository):
    with pytest.raises(KeyError):
        fragment_repository.update_transliteration(
            {'_id': 'unknown.number'},
            {'transliteration': 'transliteration'},
            None
        )


def test_statistics(database, fragment_repository, fragment):
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

    assert fragment_repository.count_transliterated_fragments() == 2
    assert fragment_repository.count_lines() == 4


def test_statistics_no_fragments(fragment_repository):
    assert fragment_repository.count_transliterated_fragments() == 0
    assert fragment_repository.count_lines() == 0


def test_search_finds_by_id(database,
                            fragment_repository,
                            fragment,
                            another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragment_repository.search(fragment['_id']) == [fragment]


def test_search_finds_by_accession(database,
                                   fragment_repository,
                                   fragment,
                                   another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragment_repository.search(fragment['accession']) == [fragment]


def test_search_finds_by_cdli(database,
                              fragment_repository,
                              fragment,
                              another_fragment):
    database[COLLECTION].insert_many([fragment, another_fragment])

    assert fragment_repository.search(fragment['cdliNumber']) == [fragment]


def test_search_not_found(fragment_repository):
    assert fragment_repository.search('K.1') == []


SEARCH_SIGNS_DATA = [
    ([['DIŠ', 'UD']], True),
    ([['KU']], True),
    ([['UD']], True),
    ([
        ['MI', 'DIŠ'],
        ['U', 'BA', 'MA']
    ], True),
    ([['IGI', 'UD']], False),
]


@pytest.mark.parametrize("signs,is_match", SEARCH_SIGNS_DATA)
def test_search_signs(signs,
                      is_match,
                      fragment_repository,
                      transliterated_fragment,
                      another_fragment):
    fragment_repository.create(transliterated_fragment)
    fragment_repository.create(another_fragment)

    result = fragment_repository.search_signs(TransliterationQuery(signs))
    expected = [transliterated_fragment] if is_match else []
    assert result == expected


def test_find_transliterated(database,
                             fragment_repository,
                             transliterated_fragment,
                             another_fragment):
    database[COLLECTION].insert_many([
        transliterated_fragment,
        another_fragment
    ])

    assert fragment_repository.find_transliterated() ==\
        [transliterated_fragment]

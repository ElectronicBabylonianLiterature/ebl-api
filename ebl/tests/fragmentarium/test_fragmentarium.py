import attr
import pytest
from freezegun import freeze_time

from ebl.dictionary.word import WordId
from ebl.errors import DataError, NotFoundError
from ebl.fragment.transliteration import (
    Transliteration
)
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory, TransliteratedFragmentFactory
)
from ebl.text.lemmatization import Lemmatization
from ebl.text.transliteration_error import TransliterationError


def test_find(fragmentarium, fragment_repository, when):
    fragment = FragmentFactory.build()
    number = fragment.number
    when(fragment_repository).find(number).thenReturn(fragment)

    assert fragmentarium.find(number) == fragment


def test_find_not_found(fragmentarium, fragment_repository, when):
    number = 'unknown id'
    when(fragment_repository).find(number).thenRaise(NotFoundError)

    with pytest.raises(NotFoundError):
        fragmentarium.find(number)


def test_find_random(fragmentarium, fragment_repository, when):
    fragment = FragmentFactory.build()
    expected = [fragment]
    when(fragment_repository).find_random().thenReturn(expected)
    assert fragmentarium.find_random() == expected


def test_find_interesting(fragmentarium, fragment_repository, when):
    fragment = FragmentFactory.build()
    expected = [fragment]
    when(fragment_repository).find_interesting().thenReturn(expected)
    assert fragmentarium.find_interesting() == expected


def test_find_latest(fragmentarium, fragment_repository, when):
    fragment = FragmentFactory.build()
    expected = [fragment]
    when(fragment_repository).find_latest().thenReturn(expected)
    assert fragmentarium.find_latest() == expected


def test_folio_pager(fragmentarium, fragment_repository, when):
    folio_name = 'WGL'
    folio_number = '2'
    number = 'K.2'
    expected = {
        'previous': {
            'fragmentNumber': 'K.1',
            'folioNumber': '1'
        },
        'next': {
            'fragmentNumber': 'K.3',
            'folioNumber': '3'
        }
    }
    (when(fragment_repository)
     .folio_pager(folio_name, folio_number, number)
     .thenReturn(expected))
    assert fragmentarium.folio_pager(folio_name, folio_number, number) ==\
        expected


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(fragmentarium,
                                user,
                                fragment_repository,
                                changelog,
                                when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    expected_fragment = transliterated_fragment.update_transliteration(
        Transliteration('1. x x\n2. x', 'updated notes', 'X X\nX'),
        user
    )

    when(fragment_repository).find(number).thenReturn(transliterated_fragment)
    when(changelog).create(
        'fragments',
        user.profile,
        transliterated_fragment.to_dict(),
        expected_fragment.to_dict()
    ).thenReturn()
    (when(fragment_repository)
     .update_transliteration(expected_fragment)
     .thenReturn())

    updated_fragment = fragmentarium.update_transliteration(
        number,
        Transliteration('1. x x\n2. x', 'updated notes'),
        user
    )
    assert updated_fragment == expected_fragment


def test_update_transliteration_invalid(fragmentarium, user):
    with pytest.raises(TransliterationError):
        fragmentarium.update_transliteration(
            'K.1',
            Transliteration('1. invalid values'),
            user
        )


def test_update_update_transliteration_not_found(fragmentarium,
                                                 user,
                                                 fragment_repository,
                                                 when):
    number = 'unknown.number'
    when(fragment_repository).find(number).thenRaise(NotFoundError)
    with pytest.raises(NotFoundError):
        fragmentarium.update_transliteration(
            number,
            Transliteration('$ (the transliteration)', 'notes'),
            user
        )


@freeze_time("2018-09-07 15:41:24.032")
def test_update_lemmatization(fragmentarium,
                              user,
                              fragment_repository,
                              changelog,
                              when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][3]['uniqueLemma'] = ['aklu I']
    lemmatization = Lemmatization.from_list(tokens)
    expected_fragment = transliterated_fragment.update_lemmatization(
        lemmatization
    )
    when(fragment_repository).find(number).thenReturn(transliterated_fragment)
    when(changelog).create(
        'fragments',
        user.profile,
        transliterated_fragment.to_dict(),
        expected_fragment.to_dict()
    ).thenReturn()
    (when(fragment_repository)
     .update_lemmatization(expected_fragment)
     .thenReturn())

    updated_fragment = fragmentarium.update_lemmatization(
        number,
        lemmatization,
        user
    )
    assert updated_fragment == expected_fragment


def test_update_update_lemmatization_not_found(fragmentarium,
                                               user,
                                               fragment_repository,
                                               when):
    number = 'K.1'
    when(fragment_repository).find(number).thenRaise(NotFoundError)
    with pytest.raises(NotFoundError):
        fragmentarium.update_lemmatization(
            number,
            Lemmatization.from_list([[{'value': '1.', 'uniqueLemma': []}]]),
            user
        )


def test_statistics(fragmentarium, fragment_repository, when):
    transliterated_fragments = 2
    lines = 4

    (when(fragment_repository)
     .count_transliterated_fragments()
     .thenReturn(transliterated_fragments))
    when(fragment_repository).count_lines().thenReturn(lines)

    assert fragmentarium.statistics() == {
        'transliteratedFragments': transliterated_fragments,
        'lines': lines
    }


def test_search(fragmentarium, fragment_repository, when):
    fragment = FragmentFactory.build()
    query = fragment.number
    when(fragment_repository).search(query).thenReturn([fragment])

    assert fragmentarium.search(query) == [fragment]


def test_search_signs(sign_list,
                      fragmentarium,
                      fragment_repository,
                      when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    atf = 'ma-tu₂'
    transliteration = Transliteration(atf)
    sign_matrix = [['MA', 'UD']]
    lines = [['6\'. [...] x mu ta-ma-tu₂']]
    expected_query = TransliterationQuery(sign_matrix)
    matching_fragments = [transliterated_fragment]

    (when(sign_list)
     .map_readings(transliteration.values)
     .thenReturn(sign_matrix))
    (when(fragment_repository)
     .search_signs(expected_query)
     .thenReturn(matching_fragments))

    expected = [
        attr.evolve(fragment, matching_lines=lines)
        for fragment in matching_fragments
    ]
    assert fragmentarium.search_signs(transliteration) == expected


def test_find_lemmas(fragmentarium,
                     dictionary,
                     word,
                     fragment_repository,
                     when):
    query = 'GI₆'
    unique_lemma = WordId(word['_id'])
    when(fragment_repository).find_lemmas(query).thenReturn([[unique_lemma]])
    when(dictionary).find(unique_lemma).thenReturn(word)

    assert fragmentarium.find_lemmas(query) == [[word]]


def test_update_references(fragmentarium,
                           bibliography,
                           user,
                           fragment_repository,
                           changelog,
                           when):

    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    expected_fragment = fragment.set_references(references)
    when(bibliography).find(reference.id).thenReturn(reference)
    when(fragment_repository).find(number).thenReturn(fragment)
    when(fragment_repository).update_references(expected_fragment).thenReturn()
    when(changelog).create(
        'fragments',
        user.profile,
        fragment.to_dict(),
        expected_fragment.to_dict()
    ).thenReturn()

    updated_fragment = fragmentarium.update_references(
        number,
        references,
        user
    )
    assert updated_fragment == expected_fragment


def test_update_references_invalid(fragmentarium,
                                   bibliography,
                                   user,
                                   fragment_repository,
                                   when):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    when(bibliography).find(reference.id).thenRaise(NotFoundError)
    when(fragment_repository).find(number).thenReturn(fragment)
    references = (reference,)

    with pytest.raises(DataError):
        fragmentarium.update_references(
            number,
            references,
            user
        )

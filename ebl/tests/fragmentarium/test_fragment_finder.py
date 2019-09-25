import pytest

from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery
from ebl.tests.factories.fragment import (
    FragmentFactory,
    TransliteratedFragmentFactory)


def test_find(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    number = fragment.number
    when(fragment_repository).find(number).thenReturn(fragment)

    assert fragment_finder.find(number) == fragment


def test_find_not_found(fragment_finder, fragment_repository, when):
    number = 'unknown id'
    when(fragment_repository).find(number).thenRaise(NotFoundError)

    with pytest.raises(NotFoundError):
        fragment_finder.find(number)


def test_find_random(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    when(fragment_repository).find_random().thenReturn([fragment])
    assert fragment_finder.find_random() == [FragmentInfo.of(fragment)]


def test_find_interesting(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    when(fragment_repository).find_interesting().thenReturn([fragment])
    assert fragment_finder.find_interesting() == [FragmentInfo.of(fragment)]


def test_folio_pager(fragment_finder, fragment_repository, when):
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
    assert fragment_finder.folio_pager(folio_name, folio_number, number) ==\
        expected


def test_search(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    query = fragment.number
    when(fragment_repository).search(query).thenReturn([fragment])

    assert fragment_finder.search(query) == [FragmentInfo.of(fragment)]


def test_search_transliteration(fragment_finder, fragment_repository, when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    sign_matrix = [['MA', 'UD']]
    query = TransliterationQuery(sign_matrix)
    matching_fragments = [transliterated_fragment]

    (when(fragment_repository)
     .search_signs(query)
     .thenReturn(matching_fragments))

    expected_lines = (('6\'. [...] x mu ta-ma-tu₂',),)
    expected = [
        FragmentInfo.of(fragment, expected_lines)
        for fragment in matching_fragments
    ]
    assert fragment_finder.search_transliteration(query) == expected


def test_find_lemmas(fragment_finder,
                     dictionary,
                     word,
                     fragment_repository,
                     when):
    query = 'GI₆'
    unique_lemma = WordId(word['_id'])
    when(fragment_repository).find_lemmas(query).thenReturn([[unique_lemma]])
    when(dictionary).find(unique_lemma).thenReturn(word)

    assert fragment_finder.find_lemmas(query) == [[word]]

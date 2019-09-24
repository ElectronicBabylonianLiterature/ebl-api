import pytest

from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.fragment import (
    FragmentFactory
)


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

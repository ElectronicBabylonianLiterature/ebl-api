import pytest
from mockito import spy2, verifyZeroInteractions, unstub


from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery
from ebl.tests.factories.fragment import (
    FragmentFactory,
    TransliteratedFragmentFactory)


@pytest.mark.parametrize('has_photo', [True, False])
def test_find_with_photo(has_photo,
                         fragment_finder,
                         fragment_repository,
                         photo_repository,
                         when):
    fragment = FragmentFactory.build()
    number = fragment.number
    (when(fragment_repository)
     .query_by_fragment_number(number)
     .thenReturn(fragment))
    (when(photo_repository)
     .query_if_file_exists(f'{number}.jpg')
     .thenReturn(has_photo))

    assert fragment_finder.find(number) == (fragment, has_photo)


def test_find_not_found(fragment_finder, fragment_repository, when):
    number = 'unknown id'
    (when(fragment_repository)
     .query_by_fragment_number(number)
     .thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_finder.find(number)


def test_find_random(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (when(fragment_repository)
     .query_random_by_transliterated()
     .thenReturn([fragment]))
    assert fragment_finder.find_random() == [FragmentInfo.of(fragment)]


def test_find_interesting(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (when(fragment_repository)
     .query_by_kuyunjik_not_transliterated_joined_or_published()
     .thenReturn([fragment]))
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
     .query_next_and_previous_folio(folio_name, folio_number, number)
     .thenReturn(expected))
    assert fragment_finder.folio_pager(folio_name, folio_number, number) == \
        expected


def test_search(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    query = fragment.number
    (when(fragment_repository)
     .query_by_fragment_cdli_or_accession_number(query)
     .thenReturn([fragment]))

    assert fragment_finder.search(query) == [FragmentInfo.of(fragment)]


GET_SEARCH_TRANSLITERATION_EMPTY_DATA = [
    ([['']], []),
    ([[''], ['']], []),
    ([['', '']], [])
]

def test_search_transliteration(fragment_finder, fragment_repository, when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    sign_matrix = [['MA', 'UD']]
    query = TransliterationQuery(sign_matrix)
    matching_fragments = [transliterated_fragment]

    (when(fragment_repository)
     .query_by_transliteration(query)
     .thenReturn(matching_fragments))

    expected_lines = (('6\'. [...] x mu ta-ma-tu₂',),)
    expected = [
        FragmentInfo.of(fragment, expected_lines)
        for fragment in matching_fragments
    ]
    assert fragment_finder.search_transliteration(query) == expected

@pytest.mark.parametrize("query, expected", GET_SEARCH_TRANSLITERATION_EMPTY_DATA)
def test_search_transliteration_empty(query, expected, fragment_finder, fragment_repository):
    spy2(fragment_repository.query_by_transliteration)
    query = TransliterationQuery(query)
    test_result = fragment_finder.search_transliteration(query)
    verifyZeroInteractions(fragment_repository)
    assert test_result == expected
    unstub()




def test_find_lemmas(fragment_finder,
                     dictionary,
                     word,
                     fragment_repository,
                     when):
    query = 'GI₆'
    unique_lemma = WordId(word['_id'])
    when(fragment_repository).query_lemmas(query).thenReturn([[unique_lemma]])
    when(dictionary).find(unique_lemma).thenReturn(word)

    assert fragment_finder.find_lemmas(query) == [[word]]


def test_find_photo(fragment_finder,
                    photo,
                    photo_repository,
                    when):
    number = FragmentNumber('K.1')
    file_name = f'{number}.jpg'
    when(photo_repository).query_by_file_name(file_name).thenReturn(photo)

    assert fragment_finder.find_photo(number) == photo


def test_find_folio(fragment_finder,
                    folio_with_allowed_scope,
                    file_repository,
                    when):
    folio = Folio('WGL', '001')
    (when(file_repository)
     .query_by_file_name(folio.file_name)
     .thenReturn(folio_with_allowed_scope))

    assert fragment_finder.find_folio(folio) == folio_with_allowed_scope

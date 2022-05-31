import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragmentarium_search_query import (
    FragmentariumSearchQuery,
)
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_infos_pagination import FragmentInfosPagination
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


@pytest.mark.parametrize("has_photo", [True, False])
def test_find(
    has_photo,
    fragment_finder,
    fragment_repository,
    photo_repository,
    parallel_line_injector,
    when,
):
    fragment = FragmentFactory.build()
    number = fragment.number
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    (when(photo_repository).query_if_file_exists(f"{number}.jpg").thenReturn(has_photo))
    expected_fragment = fragment.set_text(
        parallel_line_injector.inject_transliteration(fragment.text)
    )

    assert fragment_finder.find(number) == (expected_fragment, has_photo)


def test_find_not_found(fragment_finder, fragment_repository, when):
    number = MuseumNumber("unknown", "id")
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_finder.find(number)


def test_find_random(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (when(fragment_repository).query_random_by_transliterated().thenReturn([fragment]))
    assert fragment_finder.find_random() == [FragmentInfo.of(fragment)]


def test_find_interesting(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (when(fragment_repository).query_path_of_the_pioneers().thenReturn([fragment]))
    assert fragment_finder.find_interesting() == [FragmentInfo.of(fragment)]


def test_folio_pager(fragment_finder, fragment_repository, when):
    folio_name = "WGL"
    folio_number = "2"
    number = "K.2"
    expected = {
        "previous": {"fragmentNumber": "K.1", "folioNumber": "1"},
        "next": {"fragmentNumber": "K.3", "folioNumber": "3"},
    }
    (
        when(fragment_repository)
        .query_next_and_previous_folio(folio_name, folio_number, number)
        .thenReturn(expected)
    )
    assert fragment_finder.folio_pager(folio_name, folio_number, number) == expected


def test_fragment_finder(fragment_finder, fragment_repository, when):
    fragment_number = "1"
    expected = {"previous": "0", "next": "2"}
    (
        when(fragment_repository)
        .query_next_and_previous_fragment(fragment_number)
        .thenReturn(expected)
    )
    assert fragment_finder.fragment_pager(fragment_number) == expected


def test_search_fragmentarium_inject_document_in_fragment_infos(
    fragment_finder, when, bibliography
):
    bibliography_entry = BibliographyEntryFactory.build()
    fragment_1 = FragmentInfo.of(
        FragmentFactory.build(
            number="K.1", references=(ReferenceFactory.build(id="RN.0"),)
        )
    )
    fragment_2 = FragmentInfo.of(
        FragmentFactory.build(
            number="K.2",
            references=(
                ReferenceFactory.build(id="RN.1"),
                ReferenceFactory.build(id="RN.2"),
            ),
        )
    )
    fragment_expected_1 = fragment_1.set_references(
        [fragment_1.references[0].set_document(bibliography_entry)]
    )
    fragment_expected_2 = fragment_2.set_references(
        [
            fragment_2.references[0].set_document(bibliography_entry),
            fragment_2.references[1].set_document(bibliography_entry),
        ]
    )
    (
        when(fragment_finder)
        .search(FragmentariumSearchQuery(bibliography_id="id", pages="pages"))
        .thenReturn(FragmentInfosPagination([fragment_1, fragment_2], 2))
    )
    (when(bibliography).find("RN.0").thenReturn(bibliography_entry))
    (when(bibliography).find("RN.1").thenReturn(bibliography_entry))
    (when(bibliography).find("RN.2").thenReturn(bibliography_entry))

    assert fragment_finder.search_fragmentarium(
        FragmentariumSearchQuery(bibliography_id="id", pages="pages")
    ) == FragmentInfosPagination(
        [
            fragment_expected_1,
            fragment_expected_2,
        ],
        2,
    )


def test_search(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    query = fragment.number
    (
        when(fragment_repository)
        .query_fragmentarium(FragmentariumSearchQuery(number=query))
        .thenReturn(([fragment], 1))
    )

    assert fragment_finder.search(
        FragmentariumSearchQuery(number=query)
    ) == FragmentInfosPagination(
        [FragmentInfo.of(fragment)],
        1,
    )


def test_search_fragmentarium_transliteration(
    fragment_finder, fragment_repository, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    sign_matrix = [["MA", "UD"]]
    query = TransliterationQuery(sign_matrix)
    matching_fragments = [transliterated_fragment]

    (
        when(fragment_repository)
        .query_fragmentarium(FragmentariumSearchQuery(transliteration=query))
        .thenReturn((matching_fragments, 1))
    )

    expected_lines = parse_atf_lark("6'. [...] x# mu ta-ma;-tu₂")
    expected = FragmentInfosPagination(
        [FragmentInfo.of(fragment, expected_lines) for fragment in matching_fragments],
        1,
    )
    assert (
        fragment_finder.search_fragmentarium(
            FragmentariumSearchQuery(transliteration=query)
        )
        == expected
    )


def test_find_photo(fragment_finder, photo, photo_repository, when):
    number = "K.1"
    file_name = f"{number}.jpg"
    when(photo_repository).query_by_file_name(file_name).thenReturn(photo)

    assert fragment_finder.find_photo(number) == photo


def test_find_folio(fragment_finder, folio_with_allowed_scope, file_repository, when):
    folio = Folio("WGL", "001")
    (
        when(file_repository)
        .query_by_file_name(folio.file_name)
        .thenReturn(folio_with_allowed_scope)
    )

    assert fragment_finder.find_folio(folio) == folio_with_allowed_scope

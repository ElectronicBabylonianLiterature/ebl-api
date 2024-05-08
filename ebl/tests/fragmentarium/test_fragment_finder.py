import attr
import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_finder import ThumbnailSize
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


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
    (
        when(fragment_repository)
        .query_by_museum_number(number, None, False)
        .thenReturn(fragment)
    )
    (when(photo_repository).query_if_file_exists(f"{number}.jpg").thenReturn(has_photo))
    expected_fragment = fragment.set_text(
        parallel_line_injector.inject_transliteration(fragment.text)
    )

    assert fragment_finder.find(number) == (expected_fragment, has_photo)


@pytest.mark.parametrize("lines", [None, [], [0, 2]])
def test_find_with_lines(
    lines,
    fragment_finder,
    fragment_repository,
    when,
):
    fragment = FragmentFactory.build()
    number = fragment.number
    (
        when(fragment_repository)
        .query_by_museum_number(number, lines, False)
        .thenReturn(fragment)
    )

    assert fragment_finder.find(number, lines)[0] == fragment


@pytest.mark.parametrize("lines", [None, [], [0, 2]])
def test_find_without_lines(
    lines,
    fragment_finder,
    fragment_repository,
    when,
):
    fragment = FragmentFactory.build()
    number = fragment.number
    (
        when(fragment_repository)
        .query_by_museum_number(number, lines, True)
        .thenReturn(
            attr.evolve(fragment, text=attr.evolve(fragment.text, lines=tuple()))
        )
    )

    assert fragment_finder.find(number, lines, True)[0].text.lines == tuple()


def test_list_all_fragments(fragment_repository) -> None:
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    assert fragment_repository.list_all_fragments() == [str(fragment.number)]


def test_find_not_found(fragment_finder, fragment_repository, when):
    number = MuseumNumber("unknown", "id")
    (
        when(fragment_repository)
        .query_by_museum_number(number, None, False)
        .thenRaise(NotFoundError)
    )

    with pytest.raises(NotFoundError):
        fragment_finder.find(number)


def test_find_random(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (
        when(fragment_repository)
        .query_random_by_transliterated(tuple())
        .thenReturn([fragment])
    )
    assert fragment_finder.find_random() == [FragmentInfo.of(fragment)]


def test_find_interesting(fragment_finder, fragment_repository, when):
    fragment = FragmentFactory.build()
    (
        when(fragment_repository)
        .query_path_of_the_pioneers(tuple())
        .thenReturn([fragment])
    )
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


def test_find_photo(fragment_finder, photo, photo_repository, when):
    number = "K.1"
    file_name = f"{number}.jpg"
    when(photo_repository).query_by_file_name(file_name).thenReturn(photo)

    assert fragment_finder.find_photo(number) == photo


@pytest.mark.parametrize("thumbnail_size", ThumbnailSize)
def test_find_thumbnail(
    fragment_finder, photo, thumbnail_repository, when, thumbnail_size
):
    number = photo.filename.removesuffix(".jpg")
    file_name = f"{number}_{thumbnail_size.value}.jpg"
    when(thumbnail_repository).query_by_file_name(file_name).thenReturn(photo)

    assert fragment_finder.find_thumbnail(number, thumbnail_size) == photo


def test_find_folio(fragment_finder, folio_with_allowed_scope, file_repository, when):
    folio = Folio("WGL", "001")
    (
        when(file_repository)
        .query_by_file_name(folio.file_name)
        .thenReturn(folio_with_allowed_scope)
    )

    assert fragment_finder.find_folio(folio) == folio_with_allowed_scope

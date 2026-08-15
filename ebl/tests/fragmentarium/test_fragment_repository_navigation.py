from ebl.common.domain.scopes import Scope
import pytest

from ebl.errors import NotFoundError
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_find_random(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create_many([FragmentFactory.build(), transliterated_fragment])

    assert fragment_repository.query_random_by_transliterated() == [
        transliterated_fragment
    ]


def test_find_random_skips_restricted_fragments(fragment_repository):
    restricted_transliterated_fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    fragment_repository.create_many([restricted_transliterated_fragment])

    assert fragment_repository.query_random_by_transliterated() == []


def test_folio_pager_exception(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.query_next_and_previous_folio(
            "test", "test", MuseumNumber.of("1841-07-26.54")
        )


@pytest.mark.parametrize(
    "museum_numbers",
    [
        [
            "K.1a",
            "K.1b",
            "K.1c",
            "DT.1",
            "Rm-II.1",
            "1840.10",
            "1840.11",
            "1840.12",
            "1841.54",
            "1841.57",
            "1841.63",
            "BM.0",
            "CBS.0",
            "UM.0",
            "N.0",
            "N.1",
            "1841-57.54",
            "1841-57.57",
            "1841-57.63",
            "Asb.p",
            "Asb.q",
            "Asb.z",
            "Ashm-1878.1",
            "U.0.a",
            "U.0.b",
            "U.0.c",
            "X.0",
            "X.1",
        ]
    ],
)
def test_query_next_and_previous_fragment(museum_numbers, fragment_repository):
    for index, fragment_number in enumerate(museum_numbers):
        fragment_repository.create(
            FragmentFactory.build(number=MuseumNumber.of(fragment_number)),
            sort_key=index,
        )

    for museum_number in museum_numbers:
        results = fragment_repository.query_next_and_previous_fragment(
            MuseumNumber.of(museum_number)
        )
        previous_index = (museum_numbers.index(museum_number) - 1) % len(museum_numbers)
        next_index = (museum_numbers.index(museum_number) + 1) % len(museum_numbers)
        assert results.previous == MuseumNumber.of(museum_numbers[previous_index])
        assert results.next == MuseumNumber.of(museum_numbers[next_index])

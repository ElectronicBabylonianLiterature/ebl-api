import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.date import Date
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

MISSING = MuseumNumber.of("X.999")


def test_a_fragment_without_a_date_fetches_none(fragment_repository) -> None:
    fragment = FragmentFactory.build(date=None)
    fragment_repository.create(fragment)

    assert fragment_repository.fetch_date(fragment.number) is None


def test_a_fragment_with_a_date_fetches_it(fragment_repository) -> None:
    fragment = FragmentFactory.build()
    while fragment.date is None:
        fragment = FragmentFactory.build()
    fragment_repository.create(fragment)

    fetched = fragment_repository.fetch_date(fragment.number)

    assert isinstance(fetched, Date)
    assert fetched == fragment.date


def test_fetching_the_date_of_a_missing_fragment_is_not_found(
    fragment_repository,
) -> None:
    with pytest.raises(NotFoundError):
        fragment_repository.fetch_date(MISSING)

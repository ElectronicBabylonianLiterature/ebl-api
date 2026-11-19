from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_fragment_review_lists_are_empty_without_fragments(
    fragment_repository: FragmentRepository,
) -> None:
    assert fragment_repository.query_path_of_the_pioneers(()) == []
    assert fragment_repository.query_by_transliterated_not_revised_by_other(()) == []


def test_fragment_ocr_signs_return_only_nonempty_rows(
    fragment_repository: FragmentRepository,
) -> None:
    fragment_repository.create_many(
        [
            FragmentFactory.build(number=MuseumNumber.of("K.1"), ocred_signs=""),
            FragmentFactory.build(number=MuseumNumber.of("K.2"), ocred_signs="KU"),
        ]
    )

    assert fragment_repository.fetch_fragment_ocred_signs() == [
        {"_id": "K.2", "ocredSigns": "KU"}
    ]


def test_single_fragment_folio_navigation_wraps_to_itself(
    fragment_repository: FragmentRepository,
) -> None:
    number = MuseumNumber.of("K.1")
    fragment_repository.create(
        FragmentFactory.build(number=number, folios=Folios((Folio("TEST", "1"),)))
    )

    assert fragment_repository.query_next_and_previous_folio("TEST", "1", number) == {
        "previous": {"fragmentNumber": "K.1", "folioNumber": "1"},
        "next": {"fragmentNumber": "K.1", "folioNumber": "1"},
    }

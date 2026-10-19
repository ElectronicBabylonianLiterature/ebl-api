from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory


def test_empty_findspot_selection_excludes_unrelated_fragments(
    fragment_repository: FragmentRepository,
) -> None:
    fragment_repository.create(
        FragmentFactory.build(archaeology=Archaeology(findspot_id=123))
    )

    assert fragment_repository.count_fragments_by_findspot_ids([], ()) == {}

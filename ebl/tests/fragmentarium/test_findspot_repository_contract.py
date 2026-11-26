from typing import Sequence

import pytest

from ebl.fragmentarium.application.findspot_map_data_service import FindspotRepository
from ebl.fragmentarium.domain.findspot import Findspot


class EmptyFindspotRepository:
    def find_by_ids(self, findspot_ids: Sequence[int]) -> Sequence[Findspot]:
        return ()


def test_incomplete_explicit_repository_cannot_be_instantiated() -> None:
    repository_type = type("IncompleteFindspotRepository", (FindspotRepository,), {})

    with pytest.raises(TypeError, match="find_by_ids"):
        repository_type()


def test_repository_contract_has_no_default_lookup() -> None:
    repository: FindspotRepository = EmptyFindspotRepository()
    default_lookup = FindspotRepository.__dict__["find_by_ids"]

    assert repository.find_by_ids((1,)) == ()

    with pytest.raises(NotImplementedError):
        default_lookup(repository, (1,))

from typing import cast

from ebl.tests.factories.archaeology import FindspotFactory
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
import pytest

FINDSPOTS = cast(list[Findspot], FindspotFactory.build_batch(3))


@pytest.mark.parametrize("findspot", FINDSPOTS)
def test_create(database, findspot_repository, findspot):
    findspot_repository.create(findspot)

    assert database["findspots"].find_one(
        {"_id": findspot.id_}
    ) == FindspotSchema().dump(findspot)


def test_fetch(findspot_repository):
    for findspot in FINDSPOTS:
        findspot_repository.create(findspot)

    assert findspot_repository.find_all() == FINDSPOTS


def test_empty_findspot_selection_excludes_existing_findspots(
    findspot_repository: MongoFindspotRepository,
) -> None:
    findspot_repository.create(FINDSPOTS[0])

    assert findspot_repository.find_by_ids([]) == ()

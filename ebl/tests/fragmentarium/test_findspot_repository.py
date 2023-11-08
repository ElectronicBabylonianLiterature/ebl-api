from ebl.tests.factories.archaeology import FindspotFactory
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema
import pytest

FINDSPOTS = FindspotFactory.build_batch(3)


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

from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.provenance.application.provenance_service import ProvenanceService
from pymongo.database import Database


def test_create_and_fetch_with_map_location(
    database: Database,
    findspot_repository: MongoFindspotRepository,
    seeded_provenance_service: ProvenanceService,
) -> None:
    site = seeded_provenance_service.find_by_id("ASSUR")
    findspot = FindspotFactory.build(
        id_=4242,
        site=site,
        map_location=MapLocation(
            ("assur-1",),
            MapLocationPrecision.EXCAVATION_AREA,
            MapLocationMatchMethod.CURATED,
            "Assur Tafeln.ods",
            "2026-07-27",
        ),
    )

    findspot_repository.create(FindspotFactory.build(id_=4241, site=site))
    findspot_repository.create(findspot)

    assert database["findspots"].find_one({"_id": 4242}) == FindspotSchema(
        context={"provenance_service": seeded_provenance_service}
    ).dump(findspot)
    assert (
        next(stored for stored in findspot_repository.find_all() if stored.id_ == 4242)
        == findspot
    )

import attr

from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory


def test_create_and_fetch_with_map_location(
    database, findspot_repository, seeded_provenance_service
):
    site = seeded_provenance_service.find_by_id("ASSUR")
    findspot = attr.evolve(
        FindspotFactory.build(
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
    )

    findspot_repository.create(findspot)

    assert database["findspots"].find_one({"_id": 4242}) == FindspotSchema(
        context={"provenance_service": seeded_provenance_service}
    ).dump(findspot)
    assert findspot_repository.find_all()[0] == findspot

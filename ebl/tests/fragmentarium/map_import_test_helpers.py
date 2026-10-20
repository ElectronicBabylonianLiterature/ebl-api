from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)


def location(polygon: str) -> MapLocation:
    return MapLocation(
        (polygon,),
        MapLocationPrecision.EXCAVATION_AREA,
        MapLocationMatchMethod.CURATED,
        "source",
        "revision",
    )

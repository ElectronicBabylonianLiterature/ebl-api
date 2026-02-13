import factory

from ebl.common.domain.provenance_data import build_provenance_records
from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord


class GeoCoordinateFactory(factory.Factory):
    class Meta:
        model = GeoCoordinate

    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    uncertainty_radius_km = factory.Faker("pyfloat", min_value=0, max_value=10)
    notes = factory.Faker("sentence")


class ProvenanceRecordFactory(factory.Factory):
    class Meta:
        model = ProvenanceRecord

    id = factory.Sequence(lambda n: f"PROV_{n}")
    long_name = factory.Faker("city")
    abbreviation = factory.Faker("lexify", text="???")
    parent = None
    cigs_key = factory.Faker("lexify", text="???")
    sort_key = factory.Faker("random_int", min=0, max=100)
    coordinates = factory.SubFactory(GeoCoordinateFactory)


_PROVENANCE_BY_ID = {
    record.id: record for record in build_provenance_records()
}

DEFAULT_PROVENANCES = tuple(
    _PROVENANCE_BY_ID[id_]
    for id_ in (
        "STANDARD_TEXT",
        "ASSYRIA",
        "BABYLONIA",
        "BABYLON",
        "NINEVEH",
        "KALHU",
        "NIPPUR",
        "UR",
        "URUK",
        "PERIPHERY",
    )
)

DEFAULT_NON_STANDARD_PROVENANCES = tuple(
    record for record in DEFAULT_PROVENANCES if record.id != "STANDARD_TEXT"
)

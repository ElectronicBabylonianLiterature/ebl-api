import factory

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


DEFAULT_PROVENANCES = (
    ProvenanceRecord(id="STANDARD_TEXT", long_name="Standard Text", abbreviation="Std"),
    ProvenanceRecord(id="ASSYRIA", long_name="Assyria", abbreviation="Assa"),
    ProvenanceRecord(id="BABYLONIA", long_name="Babylonia", abbreviation="Baba"),
    ProvenanceRecord(id="BABYLON", long_name="Babylon", abbreviation="Bab", parent="Babylonia"),
    ProvenanceRecord(id="NINEVEH", long_name="Nineveh", abbreviation="Nin", parent="Assyria"),
    ProvenanceRecord(id="KALHU", long_name="Kalhu", abbreviation="Kal", parent="Assyria"),
    ProvenanceRecord(id="NIPPUR", long_name="Nippur", abbreviation="Nip", parent="Babylonia"),
    ProvenanceRecord(id="UR", long_name="Ur", abbreviation="Ur", parent="Babylonia"),
    ProvenanceRecord(id="URUK", long_name="Uruk", abbreviation="Urk", parent="Babylonia"),
    ProvenanceRecord(id="PERIPHERY", long_name="Periphery", abbreviation=""),
)

DEFAULT_NON_STANDARD_PROVENANCES = tuple(
    record
    for record in DEFAULT_PROVENANCES
    if record.id != "STANDARD_TEXT"
)

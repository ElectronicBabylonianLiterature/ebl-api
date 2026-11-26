from typing import Tuple

from factory.base import Factory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker
from ebl.tests.factories.factory_meta import FactoryMeta

from ebl.provenance.domain.provenance_model import GeoCoordinate, ProvenanceRecord


class GeoCoordinateFactory(Factory):
    class Meta(FactoryMeta):
        model = GeoCoordinate

    latitude = Faker("latitude")
    longitude = Faker("longitude")
    uncertainty_radius_km = Faker("pyfloat", min_value=0, max_value=10)
    notes = Faker("sentence")


class ProvenanceRecordFactory(Factory):
    class Meta(FactoryMeta):
        model = ProvenanceRecord

    id = Sequence(lambda n: f"PROV_{n}")
    long_name = Faker("city")
    abbreviation = Faker("lexify", text="???")
    parent = None
    cigs_key = Faker("lexify", text="???")
    sort_key = Faker("random_int", min=0, max=100)
    coordinates = SubFactory(GeoCoordinateFactory)


def build_provenance_records() -> Tuple[ProvenanceRecord, ...]:
    return (
        ProvenanceRecord(
            id="STANDARD_TEXT", long_name="Standard Text", abbreviation="Std"
        ),
        ProvenanceRecord(id="ASSYRIA", long_name="Assyria", abbreviation="Assa"),
        ProvenanceRecord(id="BABYLONIA", long_name="Babylonia", abbreviation="Baba"),
        ProvenanceRecord(
            id="BABYLON",
            long_name="Babylon",
            abbreviation="Bab",
            parent="Babylonia",
        ),
        ProvenanceRecord(
            id="NINEVEH",
            long_name="Nineveh",
            abbreviation="Nin",
            parent="Assyria",
        ),
        ProvenanceRecord(
            id="KALHU",
            long_name="Kalhu",
            abbreviation="Kal",
            parent="Assyria",
        ),
        ProvenanceRecord(
            id="NIPPUR",
            long_name="Nippur",
            abbreviation="Nip",
            parent="Babylonia",
        ),
        ProvenanceRecord(
            id="UR",
            long_name="Ur",
            abbreviation="Ur",
            parent="Babylonia",
        ),
        ProvenanceRecord(
            id="URUK",
            long_name="Uruk",
            abbreviation="Urk",
            parent="Babylonia",
        ),
        ProvenanceRecord(id="ASSUR", long_name="Assur", abbreviation="Ašš"),
        ProvenanceRecord(
            id="TELL_EL_AMARNA",
            long_name="Tell el-Amarna",
            abbreviation="Ama",
        ),
        ProvenanceRecord(id="KIS", long_name="Kish", abbreviation="Kiš"),
        ProvenanceRecord(id="PERIPHERY", long_name="Periphery", abbreviation="Per"),
    )


_PROVENANCE_BY_ID = {record.id: record for record in build_provenance_records()}

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

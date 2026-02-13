import logging
import os
from pymongo import MongoClient

from ebl.common.domain.provenance_data import build_provenance_records
from ebl.common.domain.provenance_model import GeoCoordinate
from ebl.common.application.provenance_schema import ProvenanceRecordSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


COORDINATES_MAP = {
    "ASSUR": GeoCoordinate(35.4589, 43.2597),
    "DUR_KATLIMMU": GeoCoordinate(36.8167, 40.9500),
    "HARRAN": GeoCoordinate(36.8667, 39.0333),
    "IMGUR_ENLIL": GeoCoordinate(34.3333, 43.8333),
    "KALHU": GeoCoordinate(36.1000, 43.3333),
    "KAR_TUKULTI_NINURTA": GeoCoordinate(34.5000, 43.5167),
    "KHORSABAD": GeoCoordinate(36.5000, 43.2333),
    "NINEVEH": GeoCoordinate(36.3589, 43.1522),
    "BABYLON": GeoCoordinate(32.5425, 44.4275),
    "BORSIPPA": GeoCoordinate(32.4064, 44.3489),
    "CUTHA": GeoCoordinate(33.1167, 44.5333),
    "ERIDU": GeoCoordinate(30.8167, 45.9833),
    "GIRSU": GeoCoordinate(31.4167, 46.1000),
    "ISIN": GeoCoordinate(31.9333, 45.3000),
    "KIS": GeoCoordinate(32.5333, 44.6333),
    "LAGAS": GeoCoordinate(31.3667, 46.1500),
    "LARSA": GeoCoordinate(31.3347, 45.7014),
    "NIPPUR": GeoCoordinate(32.1289, 45.2347),
    "SIPPAR": GeoCoordinate(33.1042, 44.2656),
    "UR": GeoCoordinate(30.9625, 46.1050),
    "URUK": GeoCoordinate(31.3242, 45.6358),
    "ALALAKS": GeoCoordinate(36.5333, 36.4000),
    "EBLA": GeoCoordinate(35.7975, 36.7992),
    "EMAR": GeoCoordinate(35.9167, 38.0500),
    "MARI": GeoCoordinate(34.5500, 40.8900),
    "SUSA": GeoCoordinate(32.1900, 48.2583),
    "UGARIT": GeoCoordinate(35.6014, 35.7828),
}


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def migrate_provenances():
    logger.info("Starting provenance migration...")
    database = get_database()
    collection = database["provenances"]

    existing_count = collection.count_documents({})
    if existing_count > 0:
        logger.warning(f"Collection already contains {existing_count} documents")
        logger.info("Clearing existing provenances...")
        collection.delete_many({})

    schema = ProvenanceRecordSchema()
    record_objects = build_provenance_records(COORDINATES_MAP)
    records = [schema.dump(record) for record in record_objects]

    logger.info(f"Processing {len(records)} provenance entries...")

    if records:
        collection.insert_many(records)
        logger.info(f"✓ Migrated {len(records)} provenances")
        georeferenced = sum(1 for r in records if "coordinates" in r)
        logger.info(f"✓ {georeferenced} provenances have coordinates")

    logger.info("Creating indexes...")
    collection.create_index("longName")
    collection.create_index("abbreviation")
    collection.create_index("parent")
    logger.info("✓ Indexes created")
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    migrate_provenances()

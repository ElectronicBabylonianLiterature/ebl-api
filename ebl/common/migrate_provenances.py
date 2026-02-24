import logging
import os
import json
from pathlib import Path
from pymongo import MongoClient

from ebl.common.domain.provenance_data import build_provenance_records
from ebl.common.domain.provenance_model import GeoCoordinate
from ebl.common.application.provenance_schema import ProvenanceRecordSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_provenance_geometry() -> dict:
    geometry_path = (
        Path(__file__).resolve().parent / "domain" / "provenance_geometry.json"
    )
    if not geometry_path.exists():
        return {}
    return json.loads(geometry_path.read_text(encoding="utf-8"))


def _build_polygon_coordinates_map(geometry_data: dict) -> dict:
    return {
        provenance_id: tuple(
            GeoCoordinate(
                latitude=point["latitude"],
                longitude=point["longitude"],
            )
            for point in item.get("polygonCoordinates", [])
        )
        for provenance_id, item in geometry_data.items()
        if item.get("polygonCoordinates")
    }


def _build_centroid_coordinates_map(geometry_data: dict) -> dict:
    return {
        provenance_id: GeoCoordinate(
            latitude=item["coordinates"]["latitude"],
            longitude=item["coordinates"]["longitude"],
            uncertainty_radius_km=item["coordinates"].get("uncertaintyRadiusKm"),
        )
        for provenance_id, item in geometry_data.items()
        if item.get("coordinates")
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
    geometry_data = _load_provenance_geometry()
    centroid_coordinates_map = _build_centroid_coordinates_map(geometry_data)
    polygon_coordinates_map = _build_polygon_coordinates_map(geometry_data)

    record_objects = build_provenance_records(
        centroid_coordinates_map,
        polygon_coordinates_map,
    )
    records = [schema.dump(record) for record in record_objects]

    logger.info(f"Processing {len(records)} provenance entries...")

    if records:
        collection.insert_many(records)
        logger.info(f"✓ Migrated {len(records)} provenances")
        georeferenced = sum(1 for r in records if "coordinates" in r)
        logger.info(f"✓ {georeferenced} provenances have coordinates")
        polygonal = sum(1 for r in records if "polygonCoordinates" in r)
        logger.info(f"✓ {polygonal} provenances have polygon coordinates")

    logger.info("Creating indexes...")
    collection.create_index("longName")
    collection.create_index("abbreviation")
    collection.create_index("parent")
    logger.info("✓ Indexes created")
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    migrate_provenances()

import json

from ebl.fragmentarium.application.map_artifact_storage import publish_artifact_set


def mapping_record(findspot_id: int, *polygon_ids: str) -> dict:
    return {
        "findspotId": findspot_id,
        "polygonIds": list(polygon_ids),
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "Test Tafeln.ods",
        "sourceRevision": "2026-08-05",
    }


def write_mappings(data_dir, site_id: str, records: list[dict]) -> None:
    prefix = site_id.lower()
    filename = f"{prefix}_findspot_polygon_mappings.json"
    publish_artifact_set(
        data_dir,
        prefix,
        "test-revision",
        {filename: json.dumps(records)},
    )

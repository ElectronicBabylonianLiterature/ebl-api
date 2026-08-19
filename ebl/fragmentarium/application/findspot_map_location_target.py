from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urlparse

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    ASSUR_SITE_ID,
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.provenance.infrastructure.mongo_provenance_repository import (
    COLLECTION as PROVENANCE_COLLECTION,
)
from ebl.transliteration.infrastructure.collections import FINDSPOTS_COLLECTION


APPROVED_DEVELOPMENT_DATABASE = "ebldev"
DEVELOPMENT_CLASSIFICATION = "approved-development"
EXPECTED_TOTAL_FINDSPOTS = 4031
EXPECTED_ASSUR_FINDSPOTS = 346
EXPECTED_UNRESOLVED_ASSUR_FINDSPOTS = 42
PROTECTED_TARGET_TOKENS = ("prod", "production", "stage", "staging")


@dataclass(frozen=True)
class MappingInputs:
    records: Sequence[MapLocationImportRecord]
    polygon_ids: set[str]
    previous_records: Sequence[MapLocationImportRecord] = ()


@dataclass(frozen=True)
class ExpectedFingerprint:
    total_findspots: int = EXPECTED_TOTAL_FINDSPOTS
    assur_findspots: int = EXPECTED_ASSUR_FINDSPOTS
    unresolved: int | None = None


@dataclass(frozen=True)
class DatabaseFingerprint:
    total_findspots: int
    assur_findspots: int
    mapping_records: int
    existing_mapping_findspots: int
    assur_mapping_findspots: int
    unresolved_assur_findspots: int
    total_map_locations: int
    target_map_locations: int
    target_identical_map_locations: int
    non_target_map_locations: int
    assur_provenance_exists: bool
    is_approved_development: bool


def is_local_mongo_uri(uri: str) -> bool:
    netloc = urlparse(uri).netloc.split("@")[-1]
    hosts = [host.strip("[]").split(":", 1)[0] for host in netloc.split(",") if host]
    return bool(hosts) and all(
        host in {"localhost", "127.0.0.1", "::1"} for host in hosts
    )


def is_protected_target(uri: str, database_name: str) -> bool:
    parsed = urlparse(uri)
    target_text = " ".join(
        part.casefold()
        for part in (parsed.hostname or "", parsed.path.lstrip("/"), database_name)
    )
    return any(token in target_text for token in PROTECTED_TARGET_TOKENS)


def fingerprint_database(
    database,
    inputs: MappingInputs,
    expected: ExpectedFingerprint | None = None,
) -> DatabaseFingerprint:
    expected = expected or ExpectedFingerprint()
    records, polygon_ids, previous_records = (
        inputs.records,
        inputs.polygon_ids,
        inputs.previous_records,
    )
    expected_total_findspots = expected.total_findspots
    expected_assur_findspots = expected.assur_findspots
    expected_unresolved = expected.unresolved
    findspots = database[FINDSPOTS_COLLECTION]
    assur_site_name = _assur_site_name(database)
    mapping_ids = [record.findspot_id for record in records]
    desired_by_id = {
        record.findspot_id: MapLocationSchema().dump(record.map_location)
        for record in records
    }
    previous_by_id = {
        record.findspot_id: MapLocationSchema().dump(record.map_location)
        for record in previous_records
    }
    target_docs = list(
        findspots.find(
            {"_id": {"$in": mapping_ids}}, {"_id": 1, "site": 1, "mapLocation": 1}
        )
    )
    target_ids = {doc["_id"] for doc in target_docs}
    assur_target_docs = [
        doc for doc in target_docs if doc.get("site") == assur_site_name
    ]
    target_map_locations = [
        doc for doc in target_docs if doc.get("mapLocation") is not None
    ]
    identical = [
        doc
        for doc in target_map_locations
        if doc.get("mapLocation") == desired_by_id.get(doc["_id"])
    ]
    previous_identical = [
        doc
        for doc in target_map_locations
        if doc.get("mapLocation") == previous_by_id.get(doc["_id"])
    ]
    total_findspots = findspots.count_documents({})
    assur_findspots = (
        findspots.count_documents({"site": assur_site_name}) if assur_site_name else 0
    )
    total_map_locations = findspots.count_documents({"mapLocation": {"$exists": True}})
    non_target_map_locations = findspots.count_documents(
        {"mapLocation": {"$exists": True}, "_id": {"$nin": mapping_ids}}
    )
    unresolved = assur_findspots - len(assur_target_docs)
    expected_unresolved = (
        expected_assur_findspots - len(records)
        if expected_unresolved is None
        else expected_unresolved
    )
    approved = (
        total_findspots == expected_total_findspots
        and assur_findspots == expected_assur_findspots
        and len(records) + expected_unresolved == expected_assur_findspots
        and len(target_ids) == len(records)
        and len(assur_target_docs) == len(records)
        and unresolved == expected_unresolved
        and _existing_map_locations_are_safe(
            total_map_locations,
            len(records),
            identical,
            previous_records,
            previous_identical,
        )
        and non_target_map_locations == 0
        and assur_site_name is not None
        and _all_record_polygon_ids_exist(records, polygon_ids)
    )
    return DatabaseFingerprint(
        total_findspots=total_findspots,
        assur_findspots=assur_findspots,
        mapping_records=len(records),
        existing_mapping_findspots=len(target_ids),
        assur_mapping_findspots=len(assur_target_docs),
        unresolved_assur_findspots=unresolved,
        total_map_locations=total_map_locations,
        target_map_locations=len(target_map_locations),
        target_identical_map_locations=len(identical),
        non_target_map_locations=non_target_map_locations,
        assur_provenance_exists=assur_site_name is not None,
        is_approved_development=approved,
    )


def validate_approved_development_target(
    uri: str,
    database,
    confirm_database: str | None,
    inputs: MappingInputs,
    expected: ExpectedFingerprint | None = None,
) -> DatabaseFingerprint:
    if confirm_database != APPROVED_DEVELOPMENT_DATABASE:
        raise ValueError("approved development mode requires --confirm-database ebldev")
    if database.name != APPROVED_DEVELOPMENT_DATABASE:
        raise ValueError("connected database name does not match ebldev")
    if is_protected_target(uri, database.name):
        raise ValueError("refusing protected production or staging-like target")
    fingerprint = fingerprint_database(database, inputs, expected)
    if not fingerprint.is_approved_development:
        raise ValueError("database fingerprint does not match approved ebldev dataset")
    return fingerprint


def _assur_site_name(database) -> str | None:
    record = database[PROVENANCE_COLLECTION].find_one({"_id": ASSUR_SITE_ID})
    return record.get("longName") if record else None


def _existing_map_locations_are_safe(
    total_map_locations: int,
    expected_records: int,
    identical: Sequence[dict],
    previous_records: Sequence[MapLocationImportRecord],
    previous_identical: Sequence[dict],
) -> bool:
    return (
        total_map_locations == 0
        or (
            total_map_locations == expected_records
            and len(identical) == expected_records
        )
        or (
            bool(previous_records)
            and total_map_locations == len(previous_records)
            and len(previous_identical) == len(previous_records)
        )
    )


def _all_record_polygon_ids_exist(
    records: Sequence[MapLocationImportRecord], polygon_ids: set[str]
) -> bool:
    return all(
        polygon_id in polygon_ids
        for record in records
        for polygon_id in record.map_location.polygon_ids
    )

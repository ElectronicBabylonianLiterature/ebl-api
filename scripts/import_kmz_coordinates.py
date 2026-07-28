#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pymongo import MongoClient

from ebl.provenance.application.provenance_schema import ProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.provenance.infrastructure.mongo_provenance_repository import COLLECTION

Coordinate = dict[str, float]

_IGNORABLE_APOSTROPHES = str.maketrans(
    "",
    "",
    "'`\u00b4\u02bb\u02bc\u02be\u02bf\u2018\u2019\u201b",
)
_SPACE_RE = re.compile(r"\s+")
_PARENTHETICAL_RE = re.compile(r"\(([^()]*)\)")
_BROAD_REGION_NAMES = {
    "akkad",
    "anatolia",
    "arabia",
    "assyria",
    "babylonia",
    "egypt",
    "elam",
    "hatti",
    "iran",
    "levant",
    "mesopotamia",
    "northern babylonia",
    "palestine",
    "periphery",
    "southern babylonia",
    "subartu",
    "sumer",
    "syria",
    "urartu",
}
_BROAD_REGION_IDS = {
    "AKKAD",
    "ANATOLIA",
    "ARABIA",
    "ASSYRIA",
    "BABYLONIA",
    "EGYPT",
    "ELAM",
    "HATTI",
    "IRAN",
    "LEVANT",
    "MESOPOTAMIA",
    "PERIPHERY",
    "SUBARTU",
    "SUMER",
    "SYRIA",
    "URARTU",
}


@dataclass(frozen=True)
class KmlPlacemark:
    raw_name: str
    variants: tuple[str, ...]
    geometry_type: str
    point: Coordinate | None = None
    polygon: tuple[Coordinate, ...] = ()
    ignored_reason: str | None = None

    @property
    def has_usable_point(self) -> bool:
        return self.ignored_reason is None and self.point is not None

    @property
    def has_usable_polygon(self) -> bool:
        return self.ignored_reason is None and bool(self.polygon)

    @property
    def has_usable_geometry(self) -> bool:
        return self.has_usable_point or self.has_usable_polygon


@dataclass(frozen=True)
class KmlParseResult:
    kmz_path: str
    kml_file_name: str
    placemarks: tuple[KmlPlacemark, ...]


@dataclass(frozen=True)
class ProposedUpdate:
    provenance_id: str
    long_name: str
    parent: str | None
    cigs_key: str | None
    placemark_name: str
    match_tier: str
    fields: tuple[str, ...]
    coordinate: Coordinate | None
    polygon_coordinates: tuple[Coordinate, ...]
    reason_safe: str
    reason_existing_data_preserved: str


@dataclass(frozen=True)
class SkippedRecord:
    provenance_id: str
    long_name: str
    reason: str
    placemark_name: str | None = None


@dataclass(frozen=True)
class ImportPlan:
    proposed_updates: tuple[ProposedUpdate, ...]
    review_candidates: tuple[ProposedUpdate, ...]
    skipped_records: tuple[SkippedRecord, ...]
    exact_unique_matches: int
    normalized_unique_matches: int
    ambiguous_matches: int
    unmatched_provenance_records: int
    unmatched_kmz_placemarks: int


def normalize_spaces(value: str) -> str:
    return _SPACE_RE.sub(" ", value).strip()


def remove_uncertainty_markers(value: str) -> str:
    return value.replace("?", "")


def basic_name_key(value: str) -> str:
    return normalize_spaces(remove_uncertainty_markers(value)).casefold()


def normalize_name(value: str) -> str:
    cleaned = normalize_spaces(remove_uncertainty_markers(value))
    cleaned = cleaned.translate(_IGNORABLE_APOSTROPHES)
    decomposed = unicodedata.normalize("NFD", cleaned)
    stripped = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return normalize_spaces(stripped).casefold()


def extract_name_variants(raw_name: str) -> tuple[str, ...]:
    name = normalize_spaces(raw_name)
    before_parenthesis = name.split("(", 1)[0]
    pieces = [*before_parenthesis.split("/")]
    for parenthetical in _PARENTHETICAL_RE.findall(name):
        pieces.extend(parenthetical.split("/"))

    variants: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        variant = normalize_spaces(remove_uncertainty_markers(piece))
        if variant and variant not in seen:
            variants.append(variant)
            seen.add(variant)
    return tuple(variants)


def parse_kml_coordinate(value: str) -> Coordinate:
    parts = value.strip().split(",")
    if len(parts) < 2:
        raise ValueError("KML coordinate must include longitude and latitude")

    try:
        longitude = float(parts[0])
        latitude = float(parts[1])
    except ValueError as error:
        raise ValueError("KML coordinate contains a non-numeric value") from error

    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be finite and between -90 and 90")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be finite and between -180 and 180")

    return {"latitude": latitude, "longitude": longitude}


def parse_kml_coordinate_sequence(value: str) -> tuple[Coordinate, ...]:
    coordinates = tuple(
        parse_kml_coordinate(token) for token in value.split() if token.strip()
    )
    if len(coordinates) >= 2 and coordinates[0] == coordinates[-1]:
        coordinates = coordinates[:-1]
    return coordinates


def is_broad_region_name(name: str) -> bool:
    return normalize_name(name) in _BROAD_REGION_NAMES


def is_broad_region_record(record: ProvenanceRecord) -> bool:
    return record.id in _BROAD_REGION_IDS or is_broad_region_name(record.long_name)


def parse_kmz(path: Path | str) -> KmlParseResult:
    kmz_path = Path(path)
    if not kmz_path.exists():
        raise FileNotFoundError(f"KMZ/KML file not found: {kmz_path}")

    if kmz_path.suffix.casefold() == ".kml":
        return parse_kml_bytes(kmz_path.read_bytes(), str(kmz_path), kmz_path.name)

    with zipfile.ZipFile(kmz_path) as archive:
        kml_names = [
            name
            for name in archive.namelist()
            if name.casefold().endswith(".kml") and not name.endswith("/")
        ]
        if not kml_names:
            raise ValueError(f"No KML file found inside KMZ: {kmz_path}")
        kml_file_name = next(
            (name for name in kml_names if Path(name).name.casefold() == "doc.kml"),
            sorted(kml_names)[0],
        )
        return parse_kml_bytes(
            archive.read(kml_file_name), str(kmz_path), kml_file_name
        )


def parse_kml_bytes(
    kml_bytes: bytes, kmz_path: str = "<memory>", kml_file_name: str = "doc.kml"
) -> KmlParseResult:
    root = ElementTree.fromstring(kml_bytes)
    placemarks = tuple(
        parse_placemark(placemark) for placemark in _iter(root, "Placemark")
    )
    return KmlParseResult(kmz_path, kml_file_name, placemarks)


def parse_placemark(placemark: ElementTree.Element) -> KmlPlacemark:
    raw_name = normalize_spaces(_direct_child_text(placemark, "name") or "")
    if not raw_name:
        raw_name = "<unnamed placemark>"

    point, point_invalid, point_missing = _extract_point(placemark)
    polygon, polygon_invalid, polygon_missing = _extract_polygon(placemark)
    has_line_string = any(True for _ in _iter(placemark, "LineString"))
    geometry_type = _geometry_type(point, polygon, has_line_string)

    ignored_reason = None
    if is_broad_region_name(raw_name):
        ignored_reason = "non-site KMZ placemark"
    elif not point and not polygon:
        if point_invalid or polygon_invalid:
            ignored_reason = "invalid KMZ coordinate"
        elif point_missing or polygon_missing:
            ignored_reason = "missing KMZ coordinate"
        elif has_line_string:
            ignored_reason = "LineString-only placemark"
        else:
            ignored_reason = "unsupported geometry"

    return KmlPlacemark(
        raw_name=raw_name,
        variants=extract_name_variants(raw_name),
        geometry_type=geometry_type,
        point=point,
        polygon=polygon,
        ignored_reason=ignored_reason,
    )


def load_provenance_records(collection: Any) -> tuple[ProvenanceRecord, ...]:
    documents = list(collection.find({}))
    return tuple(ProvenanceRecordSchema(many=True).load(documents))


def build_import_plan(
    records: Sequence[ProvenanceRecord],
    placemarks: Sequence[KmlPlacemark],
) -> ImportPlan:
    usable_placemarks = tuple(
        placemark for placemark in placemarks if placemark.has_usable_geometry
    )
    backend_basic = _index_records(records, basic_name_key)
    backend_normalized = _index_records(records, normalize_name)
    kmz_basic = _index_placemarks(usable_placemarks, basic_name_key)
    kmz_normalized = _index_placemarks(usable_placemarks, normalize_name)

    proposed_updates: list[ProposedUpdate] = []
    review_candidates: list[ProposedUpdate] = []
    skipped_records: list[SkippedRecord] = []
    exact_unique_matches = 0
    normalized_unique_matches = 0
    ambiguous_matches = 0
    matched_placemark_ids: set[int] = set()

    for record in records:
        if is_broad_region_record(record):
            skipped_records.append(
                SkippedRecord(record.id, record.long_name, "broad region")
            )
            continue

        match = _find_match(
            record,
            backend_basic,
            backend_normalized,
            kmz_basic,
            kmz_normalized,
        )
        tier = match["tier"]
        placemark = match["placemark"]

        if tier == "ambiguous":
            ambiguous_matches += 1
            skipped_records.append(
                SkippedRecord(record.id, record.long_name, "ambiguous match")
            )
            continue
        if placemark is None:
            skipped_records.append(
                SkippedRecord(record.id, record.long_name, "no match")
            )
            continue

        matched_placemark_ids.add(id(placemark))
        proposal, skip = _build_update_candidate(record, placemark, tier)
        if tier == "exact":
            exact_unique_matches += 1
            if proposal:
                proposed_updates.append(proposal)
            elif skip:
                skipped_records.append(skip)
        elif tier == "normalized":
            normalized_unique_matches += 1
            if proposal:
                review_candidates.append(proposal)
            elif skip:
                skipped_records.append(skip)

    unmatched_provenance_records = sum(
        1 for skipped in skipped_records if skipped.reason == "no match"
    )
    unmatched_kmz_placemarks = sum(
        1
        for placemark in usable_placemarks
        if id(placemark) not in matched_placemark_ids
    )
    return ImportPlan(
        tuple(proposed_updates),
        tuple(review_candidates),
        tuple(skipped_records),
        exact_unique_matches,
        normalized_unique_matches,
        ambiguous_matches,
        unmatched_provenance_records,
        unmatched_kmz_placemarks,
    )


def build_report(
    records: Sequence[ProvenanceRecord],
    parsed_kml: KmlParseResult,
    plan: ImportPlan,
    apply_requested: bool = False,
    applied_updates: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    skipped_counts = Counter(skipped.reason for skipped in plan.skipped_records)
    proposed_point_updates = sum(
        1 for update in plan.proposed_updates if "coordinates" in update.fields
    )
    proposed_polygon_updates = sum(
        1 for update in plan.proposed_updates if "polygonCoordinates" in update.fields
    )

    return {
        "databaseSummary": _database_summary(records),
        "kmzSummary": _kmz_summary(parsed_kml),
        "matchSummary": {
            "exactUniqueMatches": plan.exact_unique_matches,
            "normalizedUniqueMatches": plan.normalized_unique_matches,
            "ambiguousMatches": plan.ambiguous_matches,
            "unmatchedProvenanceRecords": plan.unmatched_provenance_records,
            "unmatchedKmzPlacemarks": plan.unmatched_kmz_placemarks,
            "proposedPointCoordinateUpdates": proposed_point_updates,
            "proposedPolygonCoordinateUpdates": proposed_polygon_updates,
            "normalizedReviewCandidates": len(plan.review_candidates),
        },
        "proposedUpdates": [
            _serialize_update(update) for update in plan.proposed_updates
        ],
        "normalizedReviewCandidates": [
            _serialize_update(update) for update in plan.review_candidates
        ],
        "skippedRecords": {
            "counts": dict(sorted(skipped_counts.items())),
            "records": [
                {
                    "id": skipped.provenance_id,
                    "longName": skipped.long_name,
                    "reason": skipped.reason,
                    "placemarkName": skipped.placemark_name,
                }
                for skipped in plan.skipped_records
            ],
        },
        "apply": {
            "requested": apply_requested,
            "databaseWritesPerformed": sum(
                update.get("modifiedCount", 0) for update in applied_updates
            ),
            "updates": list(applied_updates),
        },
    }


def apply_proposed_updates(
    collection: Any,
    proposed_updates: Sequence[ProposedUpdate],
    allowlist: Mapping[str, set[str] | None] | None = None,
) -> tuple[dict[str, Any], ...]:
    applied_updates: list[dict[str, Any]] = []
    for proposed_update in proposed_updates:
        if not _allowlist_allows(allowlist, proposed_update):
            applied_updates.append(
                {
                    "id": proposed_update.provenance_id,
                    "fields": list(proposed_update.fields),
                    "matchedCount": 0,
                    "modifiedCount": 0,
                    "skippedReason": "not in allowlist",
                }
            )
            continue

        update_filter = build_no_overwrite_filter(
            proposed_update.provenance_id, proposed_update.fields
        )
        update = {"$set": _build_set_update(proposed_update)}
        result = collection.update_one(update_filter, update)
        applied_updates.append(
            {
                "id": proposed_update.provenance_id,
                "fields": list(proposed_update.fields),
                "matchedCount": result.matched_count,
                "modifiedCount": result.modified_count,
            }
        )
    return tuple(applied_updates)


def build_no_overwrite_filter(
    provenance_id: str, fields: Sequence[str]
) -> dict[str, Any]:
    missing_checks = [_missing_field_filter(field) for field in fields]
    if len(missing_checks) == 1:
        return {"_id": provenance_id, **missing_checks[0]}
    return {"_id": provenance_id, "$and": missing_checks}


def run_import(
    collection: Any,
    kmz_path: Path | str,
    apply_requested: bool = False,
    allowlist: Mapping[str, set[str] | None] | None = None,
) -> dict[str, Any]:
    parsed_kml = parse_kmz(kmz_path)
    records = load_provenance_records(collection)
    plan = build_import_plan(records, parsed_kml.placemarks)
    plan = filter_plan_by_allowlist(plan, allowlist)
    applied_updates = (
        apply_proposed_updates(collection, plan.proposed_updates, allowlist)
        if apply_requested
        else ()
    )
    return build_report(records, parsed_kml, plan, apply_requested, applied_updates)


def filter_plan_by_allowlist(
    plan: ImportPlan, allowlist: Mapping[str, set[str] | None] | None
) -> ImportPlan:
    if allowlist is None:
        return plan

    exact_updates = tuple(
        update
        for update in plan.proposed_updates
        if _allowlist_allows(allowlist, update)
    )
    approved_normalized_updates = tuple(
        replace(
            update,
            reason_safe="Normalized unique match explicitly approved by field allowlist",
        )
        for update in plan.review_candidates
        if allowlist.get(update.provenance_id) is not None
        and _allowlist_allows(allowlist, update)
    )
    review_candidates = tuple(
        update
        for update in plan.review_candidates
        if allowlist.get(update.provenance_id) is None
        and _allowlist_allows(allowlist, update)
    )
    skipped_records = [
        *plan.skipped_records,
        *(
            SkippedRecord(
                update.provenance_id,
                update.long_name,
                "not in allowlist",
                update.placemark_name,
            )
            for update in chain(plan.proposed_updates, plan.review_candidates)
            if not _allowlist_allows(allowlist, update)
        ),
    ]
    return ImportPlan(
        tuple(chain(exact_updates, approved_normalized_updates)),
        review_candidates,
        tuple(skipped_records),
        plan.exact_unique_matches,
        plan.normalized_unique_matches,
        plan.ambiguous_matches,
        plan.unmatched_provenance_records,
        plan.unmatched_kmz_placemarks,
    )


def load_allowlist(path: Path | str | None) -> Mapping[str, set[str] | None] | None:
    if path is None:
        return None

    data = json.loads(Path(path).read_text())
    entries = data.get("updates", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError(
            "Allowlist must be a JSON list or an object with an updates list"
        )

    allowlist: dict[str, set[str] | None] = {}
    for entry in entries:
        if isinstance(entry, str):
            allowlist[entry] = None
            continue
        if not isinstance(entry, dict):
            raise ValueError("Allowlist entries must be strings or objects")
        provenance_id = entry.get("id") or entry.get("_id")
        if not isinstance(provenance_id, str):
            raise ValueError("Allowlist object entries require an id")
        fields = entry.get("fields")
        allowlist[provenance_id] = set(fields) if fields else None
    return allowlist


def print_text_report(report: Mapping[str, Any]) -> None:
    database_summary = report["databaseSummary"]
    kmz_summary = report["kmzSummary"]
    match_summary = report["matchSummary"]
    apply_summary = report["apply"]

    print("KMZ provenance coordinate import")
    print("Mode:", "APPLY" if apply_summary["requested"] else "DRY RUN")
    print("Database summary:")
    print(f"  total provenance records examined: {database_summary['totalRecords']}")
    print(f"  records with existing coordinates: {database_summary['withCoordinates']}")
    print(f"  records missing coordinates: {database_summary['missingCoordinates']}")
    print(
        "  records with existing polygonCoordinates: "
        f"{database_summary['withPolygonCoordinates']}"
    )
    print(
        "  records missing polygonCoordinates: "
        f"{database_summary['missingPolygonCoordinates']}"
    )
    print("KMZ summary:")
    print(f"  KMZ path: {kmz_summary['kmzPath']}")
    print(f"  KML file: {kmz_summary['kmlFileName']}")
    print(f"  total placemarks: {kmz_summary['totalPlacemarks']}")
    print(f"  usable point placemarks: {kmz_summary['usablePointPlacemarks']}")
    print(f"  usable polygon placemarks: {kmz_summary['usablePolygonPlacemarks']}")
    print(f"  ignored region labels: {kmz_summary['ignoredRegionLabels']}")
    print(f"  ignored invalid placemarks: {kmz_summary['ignoredInvalidPlacemarks']}")
    print(f"  duplicate names: {len(kmz_summary['duplicateNames'])}")
    print("Match summary:")
    for key, value in match_summary.items():
        print(f"  {key}: {value}")
    print("Proposed updates:")
    if not report["proposedUpdates"]:
        print("  none")
    for update in report["proposedUpdates"]:
        print(
            f"  {update['id']} ({update['longName']}): "
            f"{', '.join(update['fields'])} from {update['placemarkName']} "
            f"[{update['matchTier']}]"
        )
        if update["coordinate"] is not None:
            print(f"    coordinate: {update['coordinate']}")
        if update["polygonCoordinateCount"]:
            print(f"    polygon coordinate count: {update['polygonCoordinateCount']}")
        print(f"    safe: {update['reasonSafe']}")
        print(f"    preserves existing data: {update['reasonExistingDataPreserved']}")
    if report["normalizedReviewCandidates"]:
        print("Normalized review candidates:")
        for update in report["normalizedReviewCandidates"]:
            print(
                f"  {update['id']} ({update['longName']}): "
                f"{', '.join(update['fields'])} from {update['placemarkName']} "
                "[human review required]"
            )
    print("Skipped records:")
    for reason, count in report["skippedRecords"]["counts"].items():
        print(f"  {reason}: {count}")
    print(f"Database writes performed: {apply_summary['databaseWritesPerformed']}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import missing provenance coordinates from a KMZ/KML file. "
            "Defaults to dry-run mode and writes only with --apply."
        )
    )
    parser.add_argument("--kmz", required=True, help="Path to the KMZ or KML file")
    parser.add_argument(
        "--apply",
        action="store_true",
        help=("Apply approved unique missing-field updates using no-overwrite filters"),
    )
    parser.add_argument(
        "--allowlist",
        help=(
            "Optional JSON allowlist restricting proposals and apply mode. Entries "
            "may be ids or objects with id and fields; explicit fields approve "
            "normalized unique matches."
        ),
    )
    parser.add_argument(
        "--database",
        help="Optional MongoDB database name. Defaults to MONGODB_DB or the URI default.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the detailed report as JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        print(
            "MONGODB_URI is required to load provenance records; its value was not printed.",
            file=sys.stderr,
        )
        return 2

    client = MongoClient(mongo_uri)
    try:
        database = client.get_database(args.database or os.environ.get("MONGODB_DB"))
        collection = database[COLLECTION]
        report = run_import(
            collection,
            args.kmz,
            apply_requested=args.apply,
            allowlist=load_allowlist(args.allowlist),
        )
    finally:
        client.close()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


def _iter(
    element: ElementTree.Element, local_name: str
) -> Iterable[ElementTree.Element]:
    for child in element.iter():
        if _local_name(child.tag) == local_name:
            yield child


def _direct_child_text(element: ElementTree.Element, local_name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return child.text
    return None


def _first_descendant_text(element: ElementTree.Element, local_name: str) -> str | None:
    for descendant in _iter(element, local_name):
        return descendant.text
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _extract_point(
    placemark: ElementTree.Element,
) -> tuple[Coordinate | None, bool, bool]:
    missing = False
    invalid = False
    for point in _iter(placemark, "Point"):
        coordinates_text = _first_descendant_text(point, "coordinates")
        if not coordinates_text or not coordinates_text.strip():
            missing = True
            continue
        try:
            coordinates = parse_kml_coordinate_sequence(coordinates_text)
        except ValueError:
            invalid = True
            continue
        if coordinates:
            return coordinates[0], invalid, missing
        missing = True
    return None, invalid, missing


def _extract_polygon(
    placemark: ElementTree.Element,
) -> tuple[tuple[Coordinate, ...], bool, bool]:
    missing = False
    invalid = False
    for polygon in _iter(placemark, "Polygon"):
        coordinates_text = _first_descendant_text(polygon, "coordinates")
        if not coordinates_text or not coordinates_text.strip():
            missing = True
            continue
        try:
            coordinates = parse_kml_coordinate_sequence(coordinates_text)
        except ValueError:
            invalid = True
            continue
        if len(coordinates) >= 3:
            return coordinates, invalid, missing
        invalid = True
    return (), invalid, missing


def _geometry_type(
    point: Coordinate | None, polygon: Sequence[Coordinate], has_line_string: bool
) -> str:
    types: list[str] = []
    if point:
        types.append("Point")
    if polygon:
        types.append("Polygon")
    if has_line_string:
        types.append("LineString")
    return "+".join(types) if types else "Unsupported"


def _index_records(
    records: Sequence[ProvenanceRecord], key_factory
) -> dict[str, list[ProvenanceRecord]]:
    index: dict[str, list[ProvenanceRecord]] = defaultdict(list)
    for record in records:
        _append_unique_record(index[key_factory(record.long_name)], record)
    return index


def _index_placemarks(
    placemarks: Sequence[KmlPlacemark], key_factory
) -> dict[str, list[KmlPlacemark]]:
    index: dict[str, list[KmlPlacemark]] = defaultdict(list)
    for placemark in placemarks:
        for variant in placemark.variants:
            _append_unique_placemark(index[key_factory(variant)], placemark)
    return index


def _append_unique_record(records: list[ProvenanceRecord], record: ProvenanceRecord):
    if all(existing.id != record.id for existing in records):
        records.append(record)


def _append_unique_placemark(placemarks: list[KmlPlacemark], placemark: KmlPlacemark):
    if all(existing is not placemark for existing in placemarks):
        placemarks.append(placemark)


def _find_match(
    record: ProvenanceRecord,
    backend_basic: Mapping[str, Sequence[ProvenanceRecord]],
    backend_normalized: Mapping[str, Sequence[ProvenanceRecord]],
    kmz_basic: Mapping[str, Sequence[KmlPlacemark]],
    kmz_normalized: Mapping[str, Sequence[KmlPlacemark]],
) -> dict[str, Any]:
    exact_key = basic_name_key(record.long_name)
    exact_backend = backend_basic.get(exact_key, ())
    exact_kmz = kmz_basic.get(exact_key, ())
    if exact_kmz:
        if len(exact_backend) == 1 and len(exact_kmz) == 1:
            return {"tier": "exact", "placemark": exact_kmz[0]}
        return {"tier": "ambiguous", "placemark": None}

    normalized_key = normalize_name(record.long_name)
    normalized_backend = backend_normalized.get(normalized_key, ())
    normalized_kmz = kmz_normalized.get(normalized_key, ())
    if normalized_kmz:
        if len(normalized_backend) == 1 and len(normalized_kmz) == 1:
            return {"tier": "normalized", "placemark": normalized_kmz[0]}
        return {"tier": "ambiguous", "placemark": None}

    return {"tier": "unmatched", "placemark": None}


def _build_update_candidate(
    record: ProvenanceRecord, placemark: KmlPlacemark, tier: str
) -> tuple[ProposedUpdate | None, SkippedRecord | None]:
    fields: list[str] = []
    coordinate = None
    polygon_coordinates: tuple[Coordinate, ...] = ()
    skip_reasons: list[str] = []

    if placemark.point:
        if record.coordinates is None:
            fields.append("coordinates")
            coordinate = placemark.point
        else:
            skip_reasons.append("already has coordinates")

    if placemark.polygon:
        if record.polygon_coordinates is None:
            fields.append("polygonCoordinates")
            polygon_coordinates = placemark.polygon
        else:
            skip_reasons.append("already has polygonCoordinates")

    if fields:
        return (
            ProposedUpdate(
                record.id,
                record.long_name,
                record.parent,
                record.cigs_key,
                placemark.raw_name,
                tier,
                tuple(fields),
                coordinate,
                polygon_coordinates,
                "Exact unique match and every target field is currently missing"
                if tier == "exact"
                else "Normalized unique match requires human review before applying",
                "Only missing field(s) are set; the update filter requires each target field to be absent or null.",
            ),
            None,
        )

    reason = (
        ", ".join(skip_reasons) if skip_reasons else "KMZ has no usable coordinates"
    )
    return None, SkippedRecord(record.id, record.long_name, reason, placemark.raw_name)


def _database_summary(records: Sequence[ProvenanceRecord]) -> dict[str, int]:
    with_coordinates = sum(1 for record in records if record.coordinates is not None)
    with_polygon_coordinates = sum(
        1 for record in records if record.polygon_coordinates is not None
    )
    return {
        "totalRecords": len(records),
        "withCoordinates": with_coordinates,
        "missingCoordinates": len(records) - with_coordinates,
        "withPolygonCoordinates": with_polygon_coordinates,
        "missingPolygonCoordinates": len(records) - with_polygon_coordinates,
    }


def _kmz_summary(parsed_kml: KmlParseResult) -> dict[str, Any]:
    duplicate_names = [
        {"name": name, "count": count}
        for name, count in sorted(
            Counter(
                basic_name_key(placemark.raw_name)
                for placemark in parsed_kml.placemarks
            ).items()
        )
        if count > 1
    ]
    return {
        "kmzPath": parsed_kml.kmz_path,
        "kmlFileName": parsed_kml.kml_file_name,
        "totalPlacemarks": len(parsed_kml.placemarks),
        "usablePointPlacemarks": sum(
            1 for placemark in parsed_kml.placemarks if placemark.has_usable_point
        ),
        "usablePolygonPlacemarks": sum(
            1 for placemark in parsed_kml.placemarks if placemark.has_usable_polygon
        ),
        "ignoredRegionLabels": sum(
            1
            for placemark in parsed_kml.placemarks
            if placemark.ignored_reason == "non-site KMZ placemark"
        ),
        "ignoredInvalidPlacemarks": sum(
            1
            for placemark in parsed_kml.placemarks
            if placemark.ignored_reason
            in {"invalid KMZ coordinate", "missing KMZ coordinate"}
        ),
        "duplicateNames": duplicate_names,
    }


def _serialize_update(update: ProposedUpdate) -> dict[str, Any]:
    return {
        "id": update.provenance_id,
        "longName": update.long_name,
        "parent": update.parent,
        "cigsKey": update.cigs_key,
        "placemarkName": update.placemark_name,
        "matchTier": update.match_tier,
        "fields": list(update.fields),
        "coordinate": update.coordinate,
        "polygonCoordinateCount": len(update.polygon_coordinates),
        "polygonCoordinates": list(update.polygon_coordinates),
        "reasonSafe": update.reason_safe,
        "reasonExistingDataPreserved": update.reason_existing_data_preserved,
    }


def _allowlist_allows(
    allowlist: Mapping[str, set[str] | None] | None, proposed_update: ProposedUpdate
) -> bool:
    if allowlist is None:
        return True
    allowed_fields = allowlist.get(proposed_update.provenance_id)
    if proposed_update.provenance_id not in allowlist:
        return False
    return allowed_fields is None or set(proposed_update.fields) <= allowed_fields


def _build_set_update(proposed_update: ProposedUpdate) -> dict[str, Any]:
    update: dict[str, Any] = {}
    if "coordinates" in proposed_update.fields:
        update["coordinates"] = proposed_update.coordinate
    if "polygonCoordinates" in proposed_update.fields:
        update["polygonCoordinates"] = list(proposed_update.polygon_coordinates)
    return update


def _missing_field_filter(field: str) -> dict[str, Any]:
    return {"$or": [{field: {"$exists": False}}, {field: None}]}


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import os
from typing import Any, Mapping, Sequence

from pymongo import MongoClient

from ebl.provenance.application.provenance_schema import ProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.provenance.infrastructure.mongo_provenance_repository import COLLECTION
from scripts.kmz.allowlist import filter_plan_by_allowlist as filter_plan_by_allowlist
from scripts.kmz.allowlist import load_allowlist as load_allowlist
from scripts.kmz.geometry import parse_kml_coordinate as parse_kml_coordinate
from scripts.kmz.geometry import (
    parse_kml_coordinate_sequence as parse_kml_coordinate_sequence,
)
from scripts.kmz.models import Coordinate as Coordinate
from scripts.kmz.models import ImportPlan as ImportPlan
from scripts.kmz.models import KmlParseResult as KmlParseResult
from scripts.kmz.models import KmlPlacemark as KmlPlacemark
from scripts.kmz.models import ProposedUpdate as ProposedUpdate
from scripts.kmz.models import SkippedRecord as SkippedRecord
from scripts.kmz.names import basic_name_key as basic_name_key
from scripts.kmz.names import extract_name_variants as extract_name_variants
from scripts.kmz.names import is_broad_region_name as is_broad_region_name
from scripts.kmz.names import is_broad_region_record as is_broad_region_record
from scripts.kmz.names import normalize_name as normalize_name
from scripts.kmz.names import normalize_spaces as normalize_spaces
from scripts.kmz.names import remove_uncertainty_markers as remove_uncertainty_markers
from scripts.kmz.parser import parse_kml_bytes as parse_kml_bytes
from scripts.kmz.parser import parse_kmz as parse_kmz
from scripts.kmz.parser import parse_placemark as parse_placemark
from scripts.kmz.plan import build_import_plan as build_import_plan
from scripts.kmz.report import build_report as build_report
from scripts.kmz.report import print_text_report as print_text_report
from scripts.kmz.updates import apply_proposed_updates as apply_proposed_updates
from scripts.kmz.updates import build_no_overwrite_filter as build_no_overwrite_filter


__all__ = [
    "Coordinate",
    "ImportPlan",
    "KmlParseResult",
    "KmlPlacemark",
    "ProposedUpdate",
    "SkippedRecord",
    "apply_proposed_updates",
    "basic_name_key",
    "build_import_plan",
    "build_no_overwrite_filter",
    "build_report",
    "extract_name_variants",
    "filter_plan_by_allowlist",
    "is_broad_region_name",
    "is_broad_region_record",
    "load_allowlist",
    "load_provenance_records",
    "main",
    "normalize_name",
    "normalize_spaces",
    "parse_args",
    "parse_kml_bytes",
    "parse_kml_coordinate",
    "parse_kml_coordinate_sequence",
    "parse_kmz",
    "parse_placemark",
    "print_text_report",
    "remove_uncertainty_markers",
    "run_import",
]


def load_provenance_records(collection: Any) -> tuple[ProvenanceRecord, ...]:
    documents = list(collection.find({}))
    records = ProvenanceRecordSchema(many=True).load(documents)
    assert isinstance(records, list)
    return tuple(records)


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

    client: MongoClient = MongoClient(mongo_uri)
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


if __name__ == "__main__":
    raise SystemExit(main())

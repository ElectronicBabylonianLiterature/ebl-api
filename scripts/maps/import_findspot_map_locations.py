#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ebl.fragmentarium.application.findspot_map_location_target import (  # noqa: E402
    DEVELOPMENT_CLASSIFICATION,
    is_local_mongo_uri,
    validate_approved_development_target,
)
from ebl.fragmentarium.application.findspot_map_location_importer import (
    DEFAULT_INVENTORY_PATH,
    DEFAULT_MAPPINGS_PATH,
    load_import_records,
    load_polygon_inventory,
    run_import,
)  # noqa: E402
from ebl.fragmentarium.application.findspot_map_location_importer_models import (  # noqa: E402
    MapLocationImportRecord,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Aššur map locations")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write verified mappings")
    mode.add_argument(
        "--rollback",
        action="store_true",
        help="Unset verified mappings when the existing mapLocation matches",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report only; this is the default when no mode is set",
    )
    parser.add_argument(
        "--mappings",
        type=Path,
        default=DEFAULT_MAPPINGS_PATH,
        help="Path to the verified mapping JSON file",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="Path to the polygon inventory JSON file",
    )
    parser.add_argument(
        "--previous-mappings",
        type=Path,
        help="Previous mapping JSON required for exact old-to-new migration.",
    )
    parser.add_argument(
        "--previous-inventory",
        type=Path,
        help="Previous polygon inventory JSON used to validate previous mappings.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the import summary as JSON",
    )
    parser.add_argument(
        "--allow-approved-development-target",
        action="store_true",
        help="Permit the fingerprinted shared ebldev development database.",
    )
    parser.add_argument(
        "--confirm-database",
        help="Required exact database name confirmation for approved development mode.",
    )
    return parser.parse_args(argv)


def _print_summary(summary) -> None:
    print("Aššur map location importer")
    print("Database classification:", summary.database_classification)
    print(
        "Mode:",
        "DRY-RUN" if summary.dry_run else ("ROLLBACK" if summary.rollback else "APPLY"),
    )
    print("Total findspots:", summary.total_findspots)
    print("Aššur findspots:", summary.assur_findspots)
    print("Scanned:", summary.scanned)
    print("Valid:", summary.valid)
    print("Invalid:", summary.invalid)
    print("Wrong-site mappings:", summary.wrong_site)
    print("Unknown findspots:", summary.unknown_findspots)
    print("Unknown polygons:", summary.unknown_polygons)
    print("Existing:", summary.existing)
    print("New:", summary.new)
    print("Changed:", summary.changed)
    print("Skipped:", summary.skipped)
    print("Applied:", summary.applied)
    print("Unresolved Aššur findspots:", summary.unresolved_assur_findspots)
    if summary.issues:
        print("Issues:")
        for issue in summary.issues[:10]:
            print(f"  - {issue.findspot_id}: {issue.reason}")
        if len(summary.issues) > 10:
            print(f"  ... and {len(summary.issues) - 10} more")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        print(
            "Refusing to run unless MONGODB_URI targets localhost or 127.0.0.1.",
            file=sys.stderr,
        )
        return 2

    client = MongoClient(mongo_uri)
    try:
        database = client.get_database(os.environ.get("MONGODB_DB"))
        if not is_local_mongo_uri(mongo_uri):
            if not args.allow_approved_development_target:
                print(
                    "Refusing non-local MongoDB target without approved development mode.",
                    file=sys.stderr,
                )
                return 2
            polygon_ids = load_polygon_inventory(args.inventory)
            records, issues, _ = load_import_records(args.mappings, polygon_ids)
            previous_records: Sequence[MapLocationImportRecord] = ()
            if args.previous_mappings:
                if not args.previous_inventory:
                    print(
                        "Refusing approved development mode: "
                        "--previous-inventory is required with --previous-mappings.",
                        file=sys.stderr,
                    )
                    return 2
                previous_ids = load_polygon_inventory(args.previous_inventory)
                previous_records, previous_issues, _ = load_import_records(
                    args.previous_mappings, previous_ids
                )
                if previous_issues:
                    print(
                        "Refusing approved development mode: "
                        "previous mapping input is invalid.",
                        file=sys.stderr,
                    )
                    return 1
            if issues:
                print("Refusing approved development mode: mapping input is invalid.")
                return 1
            try:
                validate_approved_development_target(
                    mongo_uri,
                    database,
                    args.confirm_database,
                    records,
                    polygon_ids,
                    previous_records,
                )
            except ValueError as error:
                print(f"Refusing approved development mode: {error}", file=sys.stderr)
                return 2
            print(
                "Approved development target verified "
                f"({DEVELOPMENT_CLASSIFICATION}, database ebldev)."
            )
        summary = run_import(
            database,
            mappings_path=args.mappings,
            inventory_path=args.inventory,
            previous_mappings_path=args.previous_mappings,
            previous_inventory_path=args.previous_inventory,
            dry_run=not args.apply and not args.rollback,
            rollback=args.rollback,
        )
    finally:
        client.close()

    if args.json:
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False, default=str))
    else:
        _print_summary(summary)
    return 1 if summary.invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())

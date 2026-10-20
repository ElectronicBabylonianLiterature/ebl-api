from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from ebl.provenance.domain.provenance_model import ProvenanceRecord
from scripts.kmz.models import ImportPlan, KmlParseResult, ProposedUpdate
from scripts.kmz.names import basic_name_key


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

from types import SimpleNamespace
from zipfile import ZipFile

from ebl.provenance.application.provenance_schema import ProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import GeoCoordinate, ProvenanceRecord
from scripts.import_kmz_coordinates import (
    basic_name_key,
    build_import_plan,
    build_no_overwrite_filter,
    extract_name_variants,
    normalize_name,
    parse_kml_bytes,
    parse_kml_coordinate,
    parse_kml_coordinate_sequence,
    run_import,
)


def test_kml_coordinate_order_is_converted_to_backend_shape():
    assert parse_kml_coordinate("44.4,32.5,0") == {
        "latitude": 32.5,
        "longitude": 44.4,
    }


def test_point_parsing_skips_missing_and_invalid_coordinates():
    result = parse_kml_bytes(
        _kml(
            _point("Adab", "44.4,32.5,0"),
            _point("Missing", ""),
            _point("Invalid", "44.4,95,0"),
        )
    )

    assert result.placemarks[0].point == {"latitude": 32.5, "longitude": 44.4}
    assert result.placemarks[0].ignored_reason is None
    assert result.placemarks[1].ignored_reason == "missing KMZ coordinate"
    assert result.placemarks[2].ignored_reason == "invalid KMZ coordinate"


def test_polygon_parsing_ignores_altitude_and_removes_duplicate_closing_coordinate():
    result = parse_kml_bytes(
        _kml(
            _polygon(
                "Adab",
                "44.4,32.5,0 44.5,32.5,12 44.5,32.6,0 44.4,32.5,99",
            ),
            _polygon("Invalid", "44.4,32.5,0 44.5,95,0 44.5,32.6,0"),
        )
    )

    assert result.placemarks[0].polygon == (
        {"latitude": 32.5, "longitude": 44.4},
        {"latitude": 32.5, "longitude": 44.5},
        {"latitude": 32.6, "longitude": 44.5},
    )
    assert len(parse_kml_coordinate_sequence("44.4,32.5,0 44.4,32.5,7")) == 1
    assert result.placemarks[1].ignored_reason == "invalid KMZ coordinate"


def test_name_variant_extraction_splits_aliases_and_uncertainty_markers():
    assert extract_name_variants("Adab (Bismaya)") == ("Adab", "Bismaya")
    assert extract_name_variants("Akk\u00fb / 'Akk\u00f4 (Tell el-Fukhkhar)") == (
        "Akk\u00fb",
        "'Akk\u00f4",
        "Tell el-Fukhkhar",
    )
    assert extract_name_variants("Uruk?") == ("Uruk",)


def test_name_normalization_handles_diacritics_modifiers_case_and_whitespace():
    assert normalize_name("\u0160ibaniba") == "sibaniba"
    assert normalize_name("\u2018Anah") == "anah"
    assert normalize_name("  Akk\u00d4   ") == "akko"
    assert basic_name_key("  Adab  ") == "adab"


def test_exact_unique_match_is_eligible_for_dry_run_proposal():
    records = (ProvenanceRecord(id="ADAB", long_name="Adab", abbreviation="Ada"),)
    placemarks = parse_kml_bytes(_kml(_point("Adab", "44.4,32.5,0"))).placemarks

    plan = build_import_plan(records, placemarks)

    assert plan.exact_unique_matches == 1
    assert plan.proposed_updates[0].provenance_id == "ADAB"
    assert plan.proposed_updates[0].fields == ("coordinates",)


def test_normalized_match_is_reported_but_not_auto_proposed():
    records = (ProvenanceRecord(id="AKKO", long_name="'Akk\u00f4", abbreviation="Ako"),)
    placemarks = parse_kml_bytes(_kml(_point("Akko", "44.4,32.5,0"))).placemarks

    plan = build_import_plan(records, placemarks)

    assert plan.normalized_unique_matches == 1
    assert plan.proposed_updates == ()
    assert plan.review_candidates[0].provenance_id == "AKKO"


def test_ambiguous_match_is_skipped():
    records = (
        ProvenanceRecord(id="ADAB_1", long_name="Adab", abbreviation="Ad1"),
        ProvenanceRecord(id="ADAB_2", long_name="Adab", abbreviation="Ad2"),
    )
    placemarks = parse_kml_bytes(_kml(_point("Adab", "44.4,32.5,0"))).placemarks

    plan = build_import_plan(records, placemarks)

    assert plan.ambiguous_matches == 2
    assert plan.proposed_updates == ()
    assert {skip.reason for skip in plan.skipped_records} == {"ambiguous match"}


def test_broad_region_is_skipped():
    records = (
        ProvenanceRecord(id="BABYLONIA", long_name="Babylonia", abbreviation="Bab"),
    )
    placemarks = parse_kml_bytes(_kml(_point("Babylonia", "44.4,32.5,0"))).placemarks

    plan = build_import_plan(records, placemarks)

    assert plan.proposed_updates == ()
    assert plan.skipped_records[0].reason == "broad region"


def test_existing_coordinates_and_polygon_coordinates_are_preserved():
    records = (
        ProvenanceRecord(
            id="ADAB",
            long_name="Adab",
            abbreviation="Ada",
            coordinates=GeoCoordinate(latitude=1, longitude=2),
            polygon_coordinates=(GeoCoordinate(latitude=1, longitude=2),),
        ),
    )
    placemarks = parse_kml_bytes(
        _kml(
            _point_and_polygon(
                "Adab",
                "44.4,32.5,0",
                "44.4,32.5,0 44.5,32.5,0 44.5,32.6,0",
            )
        )
    ).placemarks

    plan = build_import_plan(records, placemarks)

    assert plan.proposed_updates == ()
    assert (
        plan.skipped_records[0].reason
        == "already has coordinates, already has polygonCoordinates"
    )


def test_dry_run_default_performs_no_writes(tmp_path):
    kmz = _kmz(tmp_path, _kml(_point("Adab", "44.4,32.5,0")))
    collection = RecordingCollection(
        [ProvenanceRecord(id="ADAB", long_name="Adab", abbreviation="Ada")]
    )

    report = run_import(collection, kmz)

    assert collection.update_calls == []
    assert report["apply"]["databaseWritesPerformed"] == 0
    assert report["matchSummary"]["proposedPointCoordinateUpdates"] == 1


def test_dry_run_allowlist_filters_proposed_updates_without_writes(tmp_path):
    kmz = _kmz(
        tmp_path,
        _kml(
            _point("Adab", "44.4,32.5,0"),
            _point("Kisurra", "45.4,33.5,0"),
        ),
    )
    collection = RecordingCollection(
        [
            ProvenanceRecord(id="ADAB", long_name="Adab", abbreviation="Ada"),
            ProvenanceRecord(id="KISURRA", long_name="Kisurra", abbreviation="Kis"),
        ]
    )

    report = run_import(collection, kmz, allowlist={"ADAB": None})

    assert collection.update_calls == []
    assert report["apply"]["databaseWritesPerformed"] == 0
    assert report["matchSummary"]["proposedPointCoordinateUpdates"] == 1
    assert [update["id"] for update in report["proposedUpdates"]] == ["ADAB"]
    assert report["skippedRecords"]["counts"]["not in allowlist"] == 1


def test_field_allowlist_approves_normalized_match_in_dry_run(tmp_path):
    kmz = _kmz(tmp_path, _kml(_point("Akko", "44.4,32.5,0")))
    collection = RecordingCollection(
        [ProvenanceRecord(id="AKKO", long_name="'Akkô", abbreviation="Ako")]
    )

    report = run_import(collection, kmz, allowlist={"AKKO": {"coordinates"}})

    assert collection.update_calls == []
    assert report["matchSummary"]["proposedPointCoordinateUpdates"] == 1
    assert report["matchSummary"]["normalizedReviewCandidates"] == 0
    assert report["proposedUpdates"][0]["id"] == "AKKO"
    assert report["proposedUpdates"][0]["matchTier"] == "normalized"
    assert report["proposedUpdates"][0]["fields"] == ["coordinates"]


def test_bare_id_allowlist_keeps_normalized_match_review_only(tmp_path):
    kmz = _kmz(tmp_path, _kml(_point("Akko", "44.4,32.5,0")))
    collection = RecordingCollection(
        [ProvenanceRecord(id="AKKO", long_name="'Akkô", abbreviation="Ako")]
    )

    report = run_import(collection, kmz, apply_requested=True, allowlist={"AKKO": None})

    assert collection.update_calls == []
    assert report["apply"]["databaseWritesPerformed"] == 0
    assert report["proposedUpdates"] == []
    assert [candidate["id"] for candidate in report["normalizedReviewCandidates"]] == [
        "AKKO"
    ]


def test_apply_field_allowlist_uses_safety_filter_for_normalized_match(tmp_path):
    kmz = _kmz(tmp_path, _kml(_point("Akko", "44.4,32.5,0")))
    collection = RecordingCollection(
        [ProvenanceRecord(id="AKKO", long_name="'Akkô", abbreviation="Ako")]
    )

    report = run_import(
        collection,
        kmz,
        apply_requested=True,
        allowlist={"AKKO": {"coordinates"}},
    )

    assert report["apply"]["databaseWritesPerformed"] == 1
    assert collection.update_calls == [
        (
            {
                "_id": "AKKO",
                "$or": [
                    {"coordinates": {"$exists": False}},
                    {"coordinates": None},
                ],
            },
            {
                "$set": {
                    "coordinates": {"latitude": 32.5, "longitude": 44.4},
                }
            },
        )
    ]


def test_apply_updates_only_exact_unique_missing_coordinates_with_safety_filter(
    tmp_path,
):
    kmz = _kmz(tmp_path, _kml(_point("Adab", "44.4,32.5,0")))
    collection = RecordingCollection(
        [ProvenanceRecord(id="ADAB", long_name="Adab", abbreviation="Ada")]
    )

    report = run_import(collection, kmz, apply_requested=True)

    assert report["apply"]["databaseWritesPerformed"] == 1
    assert collection.update_calls == [
        (
            {
                "_id": "ADAB",
                "$or": [
                    {"coordinates": {"$exists": False}},
                    {"coordinates": None},
                ],
            },
            {
                "$set": {
                    "coordinates": {"latitude": 32.5, "longitude": 44.4},
                }
            },
        )
    ]


def test_multi_field_safety_filter_requires_every_target_field_missing():
    assert build_no_overwrite_filter("ADAB", ("coordinates", "polygonCoordinates")) == {
        "_id": "ADAB",
        "$and": [
            {
                "$or": [
                    {"coordinates": {"$exists": False}},
                    {"coordinates": None},
                ]
            },
            {
                "$or": [
                    {"polygonCoordinates": {"$exists": False}},
                    {"polygonCoordinates": None},
                ]
            },
        ],
    }


class RecordingCollection:
    def __init__(self, records):
        self.documents = [ProvenanceRecordSchema().dump(record) for record in records]
        self.update_calls = []

    def find(self, query):
        assert query == {}
        return list(self.documents)

    def update_one(self, query, update):
        self.update_calls.append((query, update))
        return SimpleNamespace(matched_count=1, modified_count=1)


def _kml(*placemarks: str) -> bytes:
    body = "".join(placemarks)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2">'
        f"<Document>{body}</Document>"
        "</kml>"
    ).encode()


def _point(name: str, coordinates: str) -> str:
    return (
        f"<Placemark><name>{name}</name><Point>"
        f"<coordinates>{coordinates}</coordinates>"
        "</Point></Placemark>"
    )


def _polygon(name: str, coordinates: str) -> str:
    return (
        f"<Placemark><name>{name}</name><Polygon><outerBoundaryIs><LinearRing>"
        f"<coordinates>{coordinates}</coordinates>"
        "</LinearRing></outerBoundaryIs></Polygon></Placemark>"
    )


def _point_and_polygon(name: str, point: str, polygon: str) -> str:
    return (
        f"<Placemark><name>{name}</name>"
        f"<Point><coordinates>{point}</coordinates></Point>"
        "<Polygon><outerBoundaryIs><LinearRing>"
        f"<coordinates>{polygon}</coordinates>"
        "</LinearRing></outerBoundaryIs></Polygon></Placemark>"
    )


def _kmz(tmp_path, kml: bytes):
    path = tmp_path / "sites.kmz"
    with ZipFile(path, "w") as archive:
        archive.writestr("doc.kml", kml)
    return path

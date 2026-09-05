import json

import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.map_curated_mappings import (
    load_curated_mappings,
    merge_verified_and_curated,
)

KNOWN_POLYGON_IDS = {"assur-a", "assur-b"}


def _row(**overrides):
    row = {
        "findspotId": 1,
        "siteId": "ASSUR",
        "polygonIds": ["assur-a"],
        "matchMethod": "curated",
        "reviewer": "reviewer-handle",
        "reviewDate": "2026-08-05",
        "source": "manual review",
        "sourceRevision": "2026-08-05",
    }
    row.update(overrides)
    return row


def _write(tmp_path, rows):
    path = tmp_path / "curated.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def test_valid_reviewed_record_is_accepted(tmp_path):
    path = _write(tmp_path, [_row()])

    records = load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)

    assert records == (
        {
            "findspotId": 1,
            "polygonIds": ["assur-a"],
            "locationPrecision": "excavation-area",
            "matchMethod": "curated",
            "source": "manual review",
            "sourceRevision": "2026-08-05",
        },
    )


def test_missing_path_returns_empty():
    assert load_curated_mappings(None, "ASSUR", KNOWN_POLYGON_IDS) == ()


@pytest.mark.parametrize("field", ["reviewer", "reviewDate"])
def test_unreviewed_placeholder_row_rejected(tmp_path, field):
    path = _write(tmp_path, [_row(**{field: ""})])

    with pytest.raises(ValidationError):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_wrong_site_rejected(tmp_path):
    path = _write(tmp_path, [_row(siteId="URUK")])

    with pytest.raises(ValueError, match="siteId"):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_unknown_polygon_rejected(tmp_path):
    path = _write(tmp_path, [_row(polygonIds=["assur-z"])])

    with pytest.raises(ValueError, match="unknown polygon"):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_duplicate_findspot_rejected(tmp_path):
    path = _write(tmp_path, [_row(), _row()])

    with pytest.raises(ValueError, match="Duplicate curated findspot"):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_duplicate_polygon_within_record_rejected(tmp_path):
    path = _write(tmp_path, [_row(polygonIds=["assur-a", "assur-a"])])

    with pytest.raises(ValidationError):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_empty_polygon_array_rejected(tmp_path):
    path = _write(tmp_path, [_row(polygonIds=[])])

    with pytest.raises(ValidationError):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_unsupported_match_method_rejected(tmp_path):
    path = _write(tmp_path, [_row(matchMethod="verified-source")])

    with pytest.raises(ValidationError):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_missing_source_provenance_rejected(tmp_path):
    path = _write(tmp_path, [_row(source="")])

    with pytest.raises(ValidationError):
        load_curated_mappings(path, "ASSUR", KNOWN_POLYGON_IDS)


def test_merge_rejects_overlap_between_verified_and_curated():
    verified = ({"findspotId": 1, "polygonIds": ["assur-a"]},)
    curated = ({"findspotId": 1, "polygonIds": ["assur-b"]},)

    with pytest.raises(ValueError, match="both verified and curated"):
        merge_verified_and_curated(verified, curated)


def test_merge_combines_disjoint_sets_sorted_by_findspot_id():
    verified = ({"findspotId": 2, "polygonIds": ["assur-a"]},)
    curated = ({"findspotId": 1, "polygonIds": ["assur-b"]},)

    merged = merge_verified_and_curated(verified, curated)

    assert [record["findspotId"] for record in merged] == [1, 2]

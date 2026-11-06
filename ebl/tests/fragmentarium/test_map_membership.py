import json
from pathlib import Path

import pytest

from ebl.fragmentarium.application.map_membership import load_membership_evidence
from ebl.fragmentarium.application.map_artifact_generator import build_site_artifacts
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.application.map_source_loader import (
    MapOdsRow,
    MapPolygon,
    SiteSources,
)


def _payload(**changes: object) -> dict:
    return {
        "schemaVersion": 1,
        "source": "https://www.ebl.lmu.de/api/findspots",
        "sourceRevision": "sha256:" + "a" * 64,
        "fetchedAt": "2026-11-06T06:09:41Z",
        "etag": None,
        "findspots": [{"findspotId": 1, "siteName": "Aššur"}],
        **changes,
    }


@pytest.mark.parametrize(
    "payload,message",
    [
        ([], "schema"),
        (_payload(schemaVersion=2), "schema"),
        (_payload(schemaVersion=True), "schema"),
        (_payload(schemaVersion=1.0), "schema"),
        (_payload(source="untrusted spreadsheet"), "canonical source"),
        (_payload(sourceRevision=1), "checksum"),
        (_payload(sourceRevision="unknown"), "checksum"),
        (_payload(findspots={}), "array"),
        (_payload(findspots=[1]), "row"),
        (_payload(findspots=[{"findspotId": 1}]), "row"),
        (_payload(findspots=[{"findspotId": True, "siteName": "Aššur"}]), "int64"),
        (_payload(findspots=[{"findspotId": -1, "siteName": "Aššur"}]), "int64"),
        (_payload(findspots=[{"findspotId": 2**63, "siteName": "Aššur"}]), "int64"),
        (_payload(findspots=[{"findspotId": "1", "siteName": "Aššur"}]), "int64"),
        (_payload(findspots=[{"findspotId": 1, "siteName": 1}]), "site names"),
        (_payload(findspots=[{"findspotId": 1, "siteName": " "}]), "site names"),
    ],
)
def test_invalid_membership_evidence_is_rejected(
    tmp_path: Path, payload: object, message: str
) -> None:
    path = tmp_path / "membership.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_membership_evidence(path)


def test_membership_preserves_ambiguous_missing_and_cross_site_records(
    tmp_path: Path,
) -> None:
    rows = [
        {"findspotId": 1, "siteName": "Aššur"},
        {"findspotId": 1, "siteName": "Uruk"},
        {"findspotId": 2, "siteName": None},
        {"findspotId": 3, "siteName": "Aššur"},
        {"findspotId": 3, "siteName": "Aššur"},
        {"findspotId": 4, "siteName": "Aššur"},
        {"findspotId": 4, "siteName": None},
    ]
    path = tmp_path / "membership.json"
    path.write_text(json.dumps(_payload(findspots=rows)), encoding="utf-8")

    evidence = load_membership_evidence(path)

    assert evidence.source == "https://www.ebl.lmu.de/api/findspots"
    assert evidence.source_revision == "sha256:" + "a" * 64
    assert evidence.findspot_ids_for("Aššur") == frozenset((3,))
    assert evidence.findspot_ids_for("Uruk") == frozenset()
    assert evidence.sites_by_findspot_id[1] == frozenset(("Aššur", "Uruk"))
    assert evidence.sites_by_findspot_id[2] == frozenset((None,))


def test_committed_membership_does_not_authorize_ambiguous_uruk_rows() -> None:
    evidence = load_membership_evidence()

    assert 1 not in evidence.findspot_ids_for("Uruk")
    assert 2 not in evidence.findspot_ids_for("Uruk")


def test_spreadsheet_claim_cannot_override_authoritative_site_membership() -> None:
    sources = SiteSources(
        ods_rows=(MapOdsRow(1, site_name="Aššur", area="Area"),),
        polygons=(MapPolygon("Area", "assur-area-id", "id"),),
    )

    artifacts = build_site_artifacts(
        SITE_CONFIGS["ASSUR"], "revision-1", sources=sources
    )

    assert artifacts["mappings"] == ()
    assert artifacts["curation"][0]["membershipStatus"] == "unverified-or-conflicting"
    assert artifacts["curation"][0]["sourceRows"][0]["area"] == "Area"


def test_bare_ids_cannot_add_authoritative_membership() -> None:
    with pytest.raises(ValueError, match="lack authoritative membership"):
        build_site_artifacts(
            SITE_CONFIGS["ASSUR"],
            "revision-1",
            sources=SiteSources((), ()),
            additional_authoritative_findspot_ids={1},
        )

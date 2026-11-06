import json

import pytest

from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR
from scripts.maps import frontend_transfer_archive as transfer
from scripts.maps.frontend_transfer_contract import TransferProvenance, site_summaries
from scripts.maps.frontend_transfer_manifest import read_artifact_sets


@pytest.mark.parametrize(
    "record",
    ["1 .M N... 100644 100644 100644 a b source.py", "? new-source.json"],
)
def test_git_status_preserves_dirty_source_state(
    monkeypatch: pytest.MonkeyPatch, record: str
) -> None:
    monkeypatch.setattr(
        transfer,
        "_git",
        lambda *args: "# branch.oid " + "a" * 40 + "\n# branch.head master\n" + record,
    )
    assert transfer._git_provenance() == TransferProvenance("a" * 40, True)


@pytest.mark.parametrize("oid", ["", "(initial)", "not-a-commit"])
def test_missing_git_revision_cannot_claim_clean_provenance(
    monkeypatch: pytest.MonkeyPatch, oid: str
) -> None:
    monkeypatch.setattr(transfer, "_git", lambda *args: "# branch.oid " + oid)
    with pytest.raises(ValueError, match="committed producer revision"):
        transfer._git_provenance()


def test_missing_git_status_header_cannot_invent_a_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transfer, "_git", lambda *args: "# branch.head master")
    with pytest.raises(ValueError, match="committed producer revision"):
        transfer._git_provenance()


def test_pending_summary_preserves_conflicts_as_a_distinct_category() -> None:
    contents, revisions = read_artifact_sets(DEFAULT_OUTPUT_DIR)
    summaries = site_summaries(contents, revisions)
    pending = unresolved = conflicts = 0
    for site_id, summary in summaries.items():
        records = json.loads(
            contents[f"{site_id.lower()}_findspot_polygon_curation_template.json"]
        )
        assert summary["pendingCurationCount"] == len(records)
        assert summary["unresolvedCount"] == sum(
            row["derivationStatus"] == "unresolved" for row in records
        )
        assert summary["conflictCount"] == sum(
            row["derivationStatus"] == "conflict" for row in records
        )
        pending += len(records)
        unresolved += sum(row["derivationStatus"] == "unresolved" for row in records)
        conflicts += sum(row["derivationStatus"] == "conflict" for row in records)
    assert (pending, unresolved, conflicts) == (66, 61, 5)

from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest

from ebl.io.media.backfill_journal import (
    BackfillJournal,
    BackfillStagingJournal,
    json_bytes,
    read_document,
)
from ebl.io.media.backfill_plan_validation import validate_plan_photo
from ebl.media.application.backfill_plan import PlannedPhoto
from ebl.media.application.media_repository import MediaReader
from ebl.media.infrastructure import backfill_candidates
from ebl.tests.media.factories import photo_media
from ebl.tests.media.backfill.test_backfill_journal import HEADER, ROW


def test_rejected_sources_roundtrip_in_their_own_array() -> None:
    photo = PlannedPhoto.of(ROW)
    assert photo.document() == ROW
    assert photo.inspected_photos == ()
    assert len(photo.rejected_sources) == 1
    assert photo.attribution_evidence == {}
    assert photo.binary_validation is None
    validate_plan_photo(ROW)
    changes: dict
    for changes in (
        {"reason": 123},
        {"inspectedPhotos": {}},
        {"inspectedPhotos": [None], "rejectedSources": []},
        {"rejectedSources": []},
        {"rejectedSources": [dict(ROW["rejectedSources"][0], unrelated=True)]},
        {"rejectedSources": [dict(ROW["rejectedSources"][0], sourceId="other")]},
        {"outcome": "candidate"},
    ):
        with pytest.raises(ValueError):
            validate_plan_photo(dict(ROW, **changes))


def test_staging_is_separate_homogeneous_and_resumable(tmp_path: Path) -> None:
    path = tmp_path / "apply.jsonl"
    header = dict(HEADER, command="apply")
    with BackfillJournal(path, header, False) as journal:
        journal.stage("source", {"id": "first"})
        journal.stage("source", {"id": "second"})
        journal.append(ROW)
    staging = path.with_name(path.name + ".staging.jsonl")
    result_rows = [read_document(line) for line in path.read_bytes().splitlines()]
    assert all(row["kind"] == "photo" for row in result_rows[1:])
    staged_rows = [read_document(line) for line in staging.read_bytes().splitlines()]
    assert all(set(row) == {"sourceId", "handles"} for row in staged_rows[1:])
    with BackfillJournal(path, header, True) as journal:
        assert journal.pending == {"source": [{"id": "first"}, {"id": "second"}]}
        staging_journal = journal.staging
        assert staging_journal is not None
        with pytest.raises(ValueError, match="source identity"):
            staging_journal.append({"handles": []})
        with pytest.raises(ValueError, match="must be objects"):
            staging_journal.append({"sourceId": "source", "handles": [1]})
        journal.reconcile("source")
        assert journal.pending == {}
        journal.finish()
        with pytest.raises(ValueError, match="incomplete apply"):
            journal.stage("source", {})
        with pytest.raises(ValueError, match="incomplete apply"):
            journal.reconcile("source")
    with BackfillJournal(path, header, True) as journal:
        assert journal.completed
        assert journal.pending == {}


def test_planning_journal_does_not_accept_staging_events(tmp_path: Path) -> None:
    with BackfillJournal(tmp_path / "plan.jsonl", HEADER, False) as journal:
        with pytest.raises(ValueError, match="incomplete apply"):
            journal.stage("source", {})
        with pytest.raises(ValueError, match="incomplete apply"):
            journal.reconcile("source")


def test_resume_recovers_header_only_apply_before_companion_creation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "apply.jsonl"
    header = dict(HEADER, command="apply")
    path.write_bytes(json_bytes(dict(header, kind="header", schema=2)))
    with BackfillJournal(path, header, True) as journal:
        assert journal.pending == {}
        journal.finish()
    assert path.with_name(path.name + ".staging.jsonl").exists()


def test_failed_completed_apply_recovery_releases_companion_lock(
    tmp_path: Path,
) -> None:
    path = tmp_path / "apply.jsonl"
    header = dict(HEADER, command="apply")
    with BackfillJournal(path, header, False) as journal:
        journal.finish()
    staging_path = path.with_name(path.name + ".staging.jsonl")
    staging_path.write_bytes(staging_path.read_bytes().splitlines(keepends=True)[0])
    with pytest.raises(ValueError, match="completed staging"):
        BackfillJournal(path, header, True)
    with BackfillStagingJournal(
        staging_path, dict(header, command="apply-staging"), True
    ):
        pass


def test_inspection_validation_rejects_cross_variant_and_malformed_fields() -> None:
    inspection = {
        "fragmentId": "K.1",
        "representation": {
            "mimeType": "image/jpeg",
            "width": 1,
            "height": 1,
            "fileSize": 1,
            "sha256": "a" * 64,
        },
        "attribution": None,
        "attributionEvidence": {},
        "binaryValidation": "decoded",
    }
    changes: dict
    for changes in (
        {"reason": "wrong variant"},
        {"fragmentId": 1},
        {"representation": {}},
        {"attribution": 1},
        {"attributionEvidence": []},
        {"attributionEvidence": {"Artist": 1}},
    ):
        with pytest.raises(ValueError):
            validate_plan_photo(
                dict(
                    ROW,
                    outcome="candidate",
                    rejectedSources=[],
                    inspectedPhotos=[dict(inspection, **changes)],
                )
            )


def test_existing_outcome_requires_import_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        backfill_candidates, "candidate_media", lambda _candidate: photo_media()
    )
    with pytest.raises(ValueError, match="legacy import source"):
        backfill_candidates.existing_outcome(
            PlannedPhoto.of(ROW), cast(MediaReader, Mock())
        )

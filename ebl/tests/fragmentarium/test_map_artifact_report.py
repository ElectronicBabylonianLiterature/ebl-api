from collections import Counter
import json

import pytest

from ebl.fragmentarium.application.map_artifact_report import (
    ArtifactReportSummary,
    render_artifact_report,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


def _summary(
    source_group_count: int = 7,
    curated_mapping_count: int = 1,
    curated_source_group_count: int = 1,
) -> ArtifactReportSummary:
    summary = ArtifactReportSummary(
        source_row_count=12,
        source_group_count=source_group_count,
        verified_mapping_count=2,
        curated_mapping_count=curated_mapping_count,
        curated_source_group_count=curated_source_group_count,
        unresolved_row_count=5,
        unresolved_group_count=3,
        conflict_row_count=2,
        conflict_group_count=1,
        unresolved_labels=Counter({"Unlocated": 2, "Unknown": 1}),
    )
    return summary


def test_render_artifact_report_uses_disjoint_current_count_labels() -> None:
    report = json.loads(render_artifact_report(SITE_CONFIGS["ASSUR"], _summary()))

    assert report["schemaVersion"] == 1
    assert report["siteId"] == "ASSUR"
    assert report["counts"] == {
        "sourceRows": 12,
        "sourceGroups": 7,
        "verifiedMappings": 2,
        "curatedMappings": 1,
        "curatedMappingsWithoutSourceGroups": 0,
        "unresolvedRows": 5,
        "unresolvedGroups": 3,
        "conflictRows": 2,
        "conflictGroups": 1,
        "invalidRows": 0,
    }
    assert report["unresolvedLabels"] == [
        {"label": "Unknown", "count": 1},
        {"label": "Unlocated", "count": 2},
    ]


def test_render_artifact_report_rejects_non_disjoint_group_accounting() -> None:
    summary = _summary(source_group_count=8)

    with pytest.raises(ValueError, match="disjoint accounting"):
        render_artifact_report(SITE_CONFIGS["ASSUR"], summary)


def test_render_artifact_report_distinguishes_external_membership_evidence() -> None:
    report = json.loads(
        render_artifact_report(
            SITE_CONFIGS["ASSUR"],
            _summary(curated_mapping_count=2, curated_source_group_count=1),
        )
    )

    assert report["counts"]["curatedMappings"] == 2
    assert report["counts"]["curatedMappingsWithoutSourceGroups"] == 1

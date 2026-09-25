from collections import Counter
from dataclasses import replace

import pytest

from ebl.fragmentarium.application.map_artifact_report import (
    ArtifactReportSummary,
    render_artifact_report,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


def _summary(**changes) -> ArtifactReportSummary:
    summary = ArtifactReportSummary(
        source_row_count=12,
        source_group_count=7,
        verified_mapping_count=2,
        curated_mapping_count=1,
        curated_source_group_count=1,
        unresolved_row_count=5,
        unresolved_group_count=3,
        conflict_row_count=2,
        conflict_group_count=1,
        unresolved_labels=Counter({"Unlocated": 2, "Unknown": 1}),
    )
    return replace(summary, **changes)


def test_render_artifact_report_uses_disjoint_current_count_labels():
    report = render_artifact_report(SITE_CONFIGS["ASSUR"], _summary())

    assert "- Source rows evaluated: 12" in report
    assert "- Findspot groups evaluated: 7" in report
    assert "- Verified mappings: 2" in report
    assert "- Curated mappings: 1" in report
    assert "- Unresolved source rows: 5" in report
    assert "- Unresolved groups: 3" in report
    assert "- Source conflict rows: 2" in report
    assert "- Source conflict groups: 1" in report
    assert "- Unresolved rows:" not in report
    assert "- Source conflicts:" not in report
    assert report.index("- `Unknown`: 1") < report.index("- `Unlocated`: 2")


def test_render_artifact_report_rejects_non_disjoint_group_accounting():
    summary = _summary(source_group_count=8)

    with pytest.raises(ValueError, match="disjoint accounting"):
        render_artifact_report(SITE_CONFIGS["ASSUR"], summary)


def test_render_artifact_report_distinguishes_external_membership_evidence():
    report = render_artifact_report(
        SITE_CONFIGS["ASSUR"],
        _summary(curated_mapping_count=2, curated_source_group_count=1),
    )

    assert "- Curated mappings: 2" in report
    assert "- Curated mappings without ODS source groups: 1" in report

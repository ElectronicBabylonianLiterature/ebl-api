from collections import Counter
from dataclasses import dataclass

from ebl.fragmentarium.application.map_site_config import MapSiteConfig


@dataclass(frozen=True)
class ArtifactReportSummary:
    source_row_count: int
    source_group_count: int
    verified_mapping_count: int
    curated_mapping_count: int
    curated_source_group_count: int
    unresolved_row_count: int
    unresolved_group_count: int
    conflict_row_count: int
    conflict_group_count: int
    unresolved_labels: Counter[str]

    def validate(self) -> None:
        categorized = (
            self.verified_mapping_count
            + self.curated_source_group_count
            + self.unresolved_group_count
            + self.conflict_group_count
        )
        if (
            self.curated_source_group_count > self.curated_mapping_count
            or categorized != self.source_group_count
        ):
            raise ValueError(
                "Artifact report groups are not a disjoint accounting of source groups."
            )


def render_artifact_report(
    config: MapSiteConfig, summary: ArtifactReportSummary
) -> str:
    summary.validate()
    lines = [
        config.report_title,
        "",
        "- Generated from immutable ODS and shapefile sources.",
        f"- Source rows evaluated: {summary.source_row_count}",
        f"- Findspot groups evaluated: {summary.source_group_count}",
        f"- Verified mappings: {summary.verified_mapping_count}",
        f"- Curated mappings: {summary.curated_mapping_count}",
        *(
            [
                "- Curated mappings without ODS source groups: "
                f"{summary.curated_mapping_count - summary.curated_source_group_count}"
            ]
            if summary.curated_mapping_count > summary.curated_source_group_count
            else []
        ),
        f"- Unresolved source rows: {summary.unresolved_row_count}",
        f"- Unresolved groups: {summary.unresolved_group_count}",
        f"- Source conflict rows: {summary.conflict_row_count}",
        f"- Source conflict groups: {summary.conflict_group_count}",
        "- Invalid source rows: 0",
        "",
        "## Deterministic rule used",
        "",
        f"`{config.derivation_rule_text}`",
        "",
        "Normalization applies Unicode NFKC, trims whitespace, preserves uncertainty markers, and case-folds both sides.",
        "",
        "## Human decision required",
        "",
        "The remaining rows need scholarly curation because no unique deterministic polygon match exists.",
        "",
        config.unresolved_heading,
        "",
    ]
    lines.extend(
        f"- `{label}`: {count}"
        for label, count in sorted(summary.unresolved_labels.items())
    )
    return "\n".join(lines) + "\n"

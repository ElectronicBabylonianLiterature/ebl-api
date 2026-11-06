from collections import Counter
from dataclasses import dataclass
import json

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
    membership_source_revision: str = ""

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
    payload = {
        "schemaVersion": 1,
        "siteId": config.site_id,
        "siteName": config.site_name,
        "membershipSourceRevision": summary.membership_source_revision or None,
        "counts": {
            "sourceRows": summary.source_row_count,
            "sourceGroups": summary.source_group_count,
            "verifiedMappings": summary.verified_mapping_count,
            "curatedMappings": summary.curated_mapping_count,
            "curatedMappingsWithoutSourceGroups": summary.curated_mapping_count
            - summary.curated_source_group_count,
            "unresolvedRows": summary.unresolved_row_count,
            "unresolvedGroups": summary.unresolved_group_count,
            "conflictRows": summary.conflict_row_count,
            "conflictGroups": summary.conflict_group_count,
            "invalidRows": 0,
        },
        "deterministicRule": config.derivation_rule_text,
        "normalization": "Unicode NFKC, whitespace trimming and case folding; uncertainty markers preserved.",
        "unresolvedLabels": [
            {"label": label, "count": count}
            for label, count in sorted(summary.unresolved_labels.items())
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

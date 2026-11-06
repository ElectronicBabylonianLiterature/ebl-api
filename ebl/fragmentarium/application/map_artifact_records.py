from ebl.fragmentarium.application.map_artifact_types import (
    CurationRecord,
    SourceRowEvidence,
)
from ebl.fragmentarium.application.map_curated_mappings import CuratedMappingRecord
from ebl.fragmentarium.application.map_findspot_grouping import FindspotGroup
from ebl.fragmentarium.application.map_site_config import MapSiteConfig


def build_verified_record(
    config: MapSiteConfig, group: FindspotGroup, source_revision: str
) -> CuratedMappingRecord:
    polygon_id = group.polygon_id
    if polygon_id is None:
        raise ValueError("Verified findspot groups must identify one polygon.")
    return {
        "findspotId": group.findspot_id,
        "polygonIds": [polygon_id],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": config.source_label,
        "sourceRevision": source_revision,
    }


def build_curation_record(
    config: MapSiteConfig,
    group: FindspotGroup,
    source_revision: str,
    has_membership: bool,
) -> CurationRecord:
    row = group.representative_row
    required_decision = (
        "Resolve conflicting polygon matches across duplicate source rows."
        if group.status == "conflict"
        else "Assign a polygon ID or leave the row unresolved."
    )
    return CurationRecord(
        findspotId=group.findspot_id,
        siteId=config.site_id,
        siteName=config.site_name,
        area=row.area,
        sector=row.sector,
        building=row.building,
        map=row.map_name,
        status="needs-human-curation",
        requiredDecision=required_decision,
        polygonIds=[],
        matchMethod="curated",
        reviewer="",
        reviewDate="",
        source="human curation",
        sourceRevision=source_revision,
        derivationStatus=group.status,
        membershipStatus="confirmed" if has_membership else "unverified-or-conflicting",
        candidatePolygonIds=sorted(group.resolved_polygon_ids),
        sourceRows=[
            SourceRowEvidence(
                findspotId=item.findspot_id,
                siteName=item.site_name,
                area=item.area,
                sector=item.sector,
                building=item.building,
                map=item.map_name,
            )
            for item in group.rows
        ],
    )

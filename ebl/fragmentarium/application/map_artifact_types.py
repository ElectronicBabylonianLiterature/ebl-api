from typing import TypedDict

from ebl.fragmentarium.application.map_curated_mappings import CuratedMappingRecord
from ebl.fragmentarium.application.map_mapping_rules import DerivationRecord


class InventoryRecord(TypedDict):
    polygonId: str
    name: str
    areaName: str
    siteId: str
    siteName: str
    geometryChecksum: str


class CurationRecord(TypedDict):
    findspotId: int
    siteId: str
    siteName: str
    area: str
    sector: str
    building: str
    map: str
    status: str
    requiredDecision: str
    polygonIds: list[str]
    matchMethod: str
    reviewer: str
    reviewDate: str
    source: str
    sourceRevision: str


class SiteArtifacts(TypedDict):
    inventory: tuple[InventoryRecord, ...]
    mappings: tuple[CuratedMappingRecord, ...]
    curation: tuple[CurationRecord, ...]
    report: str
    derivations: tuple[DerivationRecord, ...]

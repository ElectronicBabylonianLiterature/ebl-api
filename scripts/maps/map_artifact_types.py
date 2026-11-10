from typing import TypedDict

from scripts.maps.map_curated_mappings import CuratedMappingRecord
from scripts.maps.map_mapping_rules import DerivationRecord


class InventoryRecord(TypedDict):
    polygonId: str
    name: str
    areaName: str
    siteId: str
    siteName: str
    geometryChecksum: str


class SourceRowEvidence(TypedDict):
    findspotId: int
    siteName: str
    area: str
    sector: str
    building: str
    map: str


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
    derivationStatus: str
    membershipStatus: str
    candidatePolygonIds: list[str]
    sourceRows: list[SourceRowEvidence]


class SiteArtifacts(TypedDict):
    inventory: tuple[InventoryRecord, ...]
    mappings: tuple[CuratedMappingRecord, ...]
    curation: tuple[CurationRecord, ...]
    report: str
    derivations: tuple[DerivationRecord, ...]

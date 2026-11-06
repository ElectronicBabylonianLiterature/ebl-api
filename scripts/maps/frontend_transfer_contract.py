from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from ebl.fragmentarium.application.map_geometry import CANONICAL_CRS
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from scripts.maps.frontend_transfer_validation import site_summary

CONTRACT_MANIFEST = "ARTIFACT_MANIFEST.json"
CONTRACT_VERSION = "ebl-map-metadata/1"
GEOMETRY_CONTRACT_VERSION = "ebl-excavation-polygons/1"
GENERATOR_VERSION = "map_artifact_generator/3"
TRANSFER_SUFFIXES = ("polygon_inventory.json", "findspot_polygon_mappings.json")


@dataclass(frozen=True)
class TransferProvenance:
    commit: str
    dirty_worktree: bool


def transfer_names() -> tuple[str, ...]:
    return tuple(
        f"{site_id.lower()}_{suffix}"
        for site_id in SITE_CONFIGS
        for suffix in TRANSFER_SUFFIXES
    )


def site_summaries(
    contents: dict[str, bytes], revisions: dict[str, str]
) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    all_findspot_ids: set[int] = set()
    for site_id in SITE_CONFIGS:
        summary, findspot_ids = site_summary(contents, revisions, site_id)
        if all_findspot_ids & findspot_ids:
            raise ValueError("Findspot IDs must be unique across sites")
        all_findspot_ids.update(findspot_ids)
        summaries[site_id] = summary
    return summaries


def expectations(
    summaries: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {
        site_id.lower(): {
            "features": summary["polygonCount"],
            "inventory": summary["polygonCount"],
            "mappings": summary["mappingCount"],
            "mapped": summary["distinctMappedPolygonCount"],
        }
        for site_id, summary in summaries.items()
    }


def build_contract_manifest(
    contents: dict[str, bytes],
    revisions: dict[str, str],
    provenance: TransferProvenance,
) -> bytes:
    summaries = site_summaries(contents, revisions)
    payload: dict[str, object] = {
        "schemaVersion": 1,
        "contractVersion": CONTRACT_VERSION,
        "geometryContractVersion": GEOMETRY_CONTRACT_VERSION,
        "canonicalCrs": CANONICAL_CRS,
        "geometryIncluded": False,
        "generatorVersion": GENERATOR_VERSION,
        "sites": summaries,
        "expectations": expectations(summaries),
        "fileChecksums": {
            name: hashlib.sha256(contents[name]).hexdigest()
            for name in transfer_names()
        },
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    payload["contractRevision"] = (
        "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    )
    payload["producer"] = {
        "repository": "ElectronicBabylonianLiterature/ebl-api",
        "commit": provenance.commit,
        "dirtyWorktree": provenance.dirty_worktree,
    }
    return (
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()

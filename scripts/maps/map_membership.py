from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import re

from ebl.common.query.parameter_parser import MAX_FINDSPOT_ID
from ebl.fragmentarium.application.map_json import load_strict_json

MEMBERSHIP_PATH = Path(__file__).resolve().parent / "data/map_site_membership.v1.json"


@dataclass(frozen=True)
class MembershipEvidence:
    source: str
    source_revision: str
    sites_by_findspot_id: Mapping[int, frozenset[str | None]]

    def findspot_ids_for(self, site_name: str) -> frozenset[int]:
        return frozenset(
            findspot_id
            for findspot_id, sites in self.sites_by_findspot_id.items()
            if sites == frozenset((site_name,))
        )


def load_membership_evidence(path: Path = MEMBERSHIP_PATH) -> MembershipEvidence:
    payload = load_strict_json(path.read_text(encoding="utf-8"), str(path))
    if not isinstance(payload, dict):
        raise ValueError("Unsupported map membership evidence schema.")
    if type(payload.get("schemaVersion")) is not int or payload["schemaVersion"] != 1:
        raise ValueError("Unsupported map membership evidence schema.")
    source, revision = payload.get("source"), payload.get("sourceRevision")
    if source != "https://www.ebl.lmu.de/api/findspots":
        raise ValueError("Map membership evidence must identify the canonical source.")
    if not isinstance(revision, str) or not re.fullmatch(
        r"sha256:[a-f0-9]{64}", revision
    ):
        raise ValueError("Map membership evidence requires a source response checksum.")
    rows = payload.get("findspots")
    if not isinstance(rows, list):
        raise ValueError("Map membership evidence findspots must be an array.")
    sites_by_id: dict[int, set[str | None]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"findspotId", "siteName"}:
            raise ValueError("Invalid map membership evidence row.")
        findspot_id, site = row["findspotId"], row["siteName"]
        if (
            isinstance(findspot_id, bool)
            or not isinstance(findspot_id, int)
            or not 0 <= findspot_id <= MAX_FINDSPOT_ID
        ):
            raise ValueError(
                "Map membership evidence requires BSON int64 findspot IDs."
            )
        if site is not None and (not isinstance(site, str) or not site.strip()):
            raise ValueError(
                "Map membership site names must be nonblank strings or null."
            )
        sites_by_id.setdefault(findspot_id, set()).add(site)
    return MembershipEvidence(
        source, revision, {key: frozenset(sites) for key, sites in sites_by_id.items()}
    )

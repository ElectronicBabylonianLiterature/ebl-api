from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.domain.map_location import MapLocation


class MapArtifactRepository:
    """Read-only crosswalk from findspot ID to MapLocation, sourced from the
    version-controlled generated mapping artifacts rather than MongoDB."""

    def __init__(self, data_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
        self._data_dir = data_dir

    def known_site_ids(self) -> tuple[str, ...]:
        return tuple(
            site_id for site_id in SITE_CONFIGS if self._mappings_path(site_id).exists()
        )

    def load_site_map_locations(self, site_id: str) -> dict[int, MapLocation]:
        path = self._mappings_path(site_id)
        if site_id not in SITE_CONFIGS or not path.exists():
            return {}
        entries = json.loads(path.read_text(encoding="utf-8"))
        schema = MapLocationSchema()
        return {entry["findspotId"]: schema.load(entry) for entry in entries}

    def load_map_locations(
        self, site_ids: Sequence[str] | None = None
    ) -> dict[int, MapLocation]:
        target_ids = site_ids if site_ids is not None else self.known_site_ids()
        locations: dict[int, MapLocation] = {}
        for site_id in target_ids:
            locations.update(self.load_site_map_locations(site_id))
        return locations

    def _mappings_path(self, site_id: str) -> Path:
        return self._data_dir / f"{site_id.lower()}_findspot_polygon_mappings.json"

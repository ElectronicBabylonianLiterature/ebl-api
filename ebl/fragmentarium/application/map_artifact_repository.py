from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ebl.fragmentarium.application.map_artifact_storage import (
    artifact_manifest_name,
    read_validated_artifact,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.fragmentarium.application.map_json import load_strict_json
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from ebl.fragmentarium.domain.map_location import MapLocation

MAX_FINDSPOT_ID = 2**63 - 1


@dataclass(frozen=True)
class SiteMapLocation:
    site_id: str
    location: MapLocation


class MapArtifactRepository:
    """Read-only, validated findspot-to-map-location artifact repository."""

    def __init__(self, data_dir: Path = MAP_DATA_DIR) -> None:
        self._data_dir = data_dir.resolve()

    def known_site_ids(self) -> tuple[str, ...]:
        return tuple(
            site_id
            for site_id in SITE_CONFIGS
            if (self._data_dir / artifact_manifest_name(site_id.lower())).is_file()
        )

    @staticmethod
    def supports_site(site_id: str) -> bool:
        return site_id in SITE_CONFIGS

    @staticmethod
    def site_name(site_id: str) -> str:
        MapArtifactRepository._require_known_site(site_id)
        return SITE_CONFIGS[site_id].site_name

    def load_site_map_locations(self, site_id: str) -> dict[int, SiteMapLocation]:
        self._require_known_site(site_id)
        filename = self._mappings_filename(site_id)
        raw = read_validated_artifact(self._data_dir, site_id.lower(), filename)
        entries = load_strict_json(raw, filename)
        if not isinstance(entries, list):
            raise ValueError(f"Map mappings for {site_id} must be a JSON array.")

        locations: dict[int, SiteMapLocation] = {}
        schema = MapLocationSchema()
        for index, entry in enumerate(entries):
            findspot_id, location = self._load_entry(schema, site_id, index, entry)
            if findspot_id in locations:
                raise ValueError(
                    f"Duplicate findspot ID {findspot_id} in {site_id} mappings."
                )
            locations[findspot_id] = SiteMapLocation(site_id, location)
        return locations

    def load_map_locations(
        self, site_ids: Sequence[str] | None = None
    ) -> dict[int, SiteMapLocation]:
        target_ids = tuple(site_ids) if site_ids is not None else self.known_site_ids()
        locations: dict[int, SiteMapLocation] = {}
        for site_id in target_ids:
            for findspot_id, site_location in self.load_site_map_locations(
                site_id
            ).items():
                existing = locations.get(findspot_id)
                if existing is not None:
                    raise ValueError(
                        f"Duplicate findspot ID {findspot_id} across sites "
                        f"{existing.site_id} and {site_id}."
                    )
                locations[findspot_id] = site_location
        return locations

    @staticmethod
    def _load_entry(
        schema: MapLocationSchema, site_id: str, index: int, entry: object
    ) -> tuple[int, MapLocation]:
        if not isinstance(entry, dict):
            raise ValueError(
                f"Map mapping {index} for {site_id} must be a JSON object."
            )
        if "findspotId" not in entry:
            raise ValueError(f"Map mapping {index} for {site_id} has no findspotId.")
        findspot_id = entry["findspotId"]
        if (
            isinstance(findspot_id, bool)
            or not isinstance(findspot_id, int)
            or not 0 <= findspot_id <= MAX_FINDSPOT_ID
        ):
            raise ValueError(
                f"Map mapping {index} for {site_id} has an invalid findspotId."
            )
        payload = {key: value for key, value in entry.items() if key != "findspotId"}
        return findspot_id, schema.load(payload)

    @staticmethod
    def _require_known_site(site_id: str) -> None:
        if site_id not in SITE_CONFIGS:
            raise ValueError(f"Unknown map site ID: {site_id!r}.")

    @staticmethod
    def _mappings_filename(site_id: str) -> str:
        return f"{site_id.lower()}_findspot_polygon_mappings.json"

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

import attr

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
)
from ebl.fragmentarium.domain.findspot import Findspot

MAX_JSON_SAFE_INTEGER = 2**53 - 1


class FindspotRepository(Protocol):
    def find_by_ids(self, findspot_ids: Sequence[int]) -> Sequence[Findspot]: ...


@dataclass(frozen=True)
class FindspotMapData:
    findspot: Findspot
    site_id: str
    site_name: str
    accessible_fragment_count: int


class FindspotMapDataService:
    """Serves map-data from the version-controlled, read-only findspot-to-polygon
    mapping artifacts, joined at request time against live Findspot metadata and
    authorization-filtered fragment counts. No mapLocation value is read from or
    written to MongoDB by this service."""

    def __init__(
        self,
        findspot_repository: FindspotRepository,
        fragment_repository: FragmentRepository,
        map_artifact_repository: Optional[MapArtifactRepository] = None,
    ) -> None:
        self._findspot_repository = findspot_repository
        self._fragment_repository = fragment_repository
        self._map_artifact_repository = (
            map_artifact_repository or MapArtifactRepository()
        )

    def find_map_data(
        self,
        site_id: Optional[str] = None,
        user_scopes: Sequence[Scope] = (),
        script_period: Optional[str] = None,
        script_period_modifier: Optional[str] = None,
        genre: Optional[Sequence[str]] = None,
    ) -> Sequence[FindspotMapData]:
        if site_id is not None and not self._map_artifact_repository.supports_site(
            site_id
        ):
            return []
        map_locations = self._map_artifact_repository.load_map_locations(
            (site_id,) if site_id is not None else None
        )
        if not map_locations:
            return []
        if any(findspot_id > MAX_JSON_SAFE_INTEGER for findspot_id in map_locations):
            raise ValueError("Map findspot IDs must be JSON-safe integers.")

        findspots = sorted(
            (
                attr.evolve(findspot, map_location=map_locations[findspot.id_].location)
                for findspot in self._findspot_repository.find_by_ids(
                    tuple(map_locations)
                )
                if findspot.site is not None
                and findspot.site.id == map_locations[findspot.id_].site_id
                and (site_id is None or findspot.site.id == site_id)
            ),
            key=lambda findspot: findspot.id_,
        )

        counts = self._fragment_repository.count_fragments_by_findspot_ids(
            [findspot.id_ for findspot in findspots],
            user_scopes,
            script_period,
            script_period_modifier,
            genre,
        )
        result = []
        for findspot in findspots:
            count = counts.get(findspot.id_, 0)
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or not 0 <= count <= MAX_JSON_SAFE_INTEGER
            ):
                raise ValueError("Map fragment counts must be JSON-safe integers.")
            site_id = map_locations[findspot.id_].site_id
            result.append(
                FindspotMapData(
                    findspot,
                    site_id,
                    self._map_artifact_repository.site_name(site_id),
                    count,
                )
            )
        return result

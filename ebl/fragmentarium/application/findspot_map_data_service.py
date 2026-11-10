from abc import abstractmethod
from dataclasses import dataclass
import logging
from threading import Lock
from typing import Optional, Protocol, Sequence

import attr

from ebl.common.domain.scopes import Scope
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.fragmentarium.domain.map_location import MapLocation

MAX_JSON_SAFE_INTEGER = 2**53 - 1
MAX_REPORTED_DROPPED_SETS = 128
LOGGER = logging.getLogger(__name__)


class FindspotRepository(Protocol):
    @abstractmethod
    def find_by_ids(self, findspot_ids: Sequence[int]) -> Sequence[Findspot]:
        raise NotImplementedError


@dataclass(frozen=True)
class FindspotMapData:
    findspot: Findspot
    site_id: str
    site_name: str
    accessible_fragment_count: int

    @property
    def map_location(self) -> MapLocation:
        location = self.findspot.map_location
        if location is None:
            raise ValueError("Map-data rows require a validated map location.")
        return location


class FindspotMapDataService:
    def __init__(
        self,
        findspot_repository: FindspotRepository,
        fragment_repository: FragmentRepository,
        map_artifact_repository: MapArtifactRepository,
    ) -> None:
        self._findspot_repository = findspot_repository
        self._fragment_repository = fragment_repository
        self._map_artifact_repository = map_artifact_repository
        self._reported_dropped_ids: dict[frozenset[int], None] = {}
        self._warning_lock = Lock()

    def find_map_data(
        self,
        site_id: Optional[str] = None,
        user_scopes: Sequence[Scope] = (),
        script_period: Optional[str] = None,
        script_period_modifier: Optional[str] = None,
        genre: Optional[Sequence[str]] = None,
    ) -> Sequence[FindspotMapData]:
        if site_id is not None:
            if not self._map_artifact_repository.supports_site(site_id):
                return []
            if site_id not in self._map_artifact_repository.known_site_ids():
                raise NotFoundError(
                    f"Map artifacts are not published for site {site_id}."
                )
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
        self._warn_dropped_findspots(
            frozenset(map_locations) - {findspot.id_ for findspot in findspots}
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
            mapped_site_id = map_locations[findspot.id_].site_id
            result.append(
                FindspotMapData(
                    findspot,
                    mapped_site_id,
                    self._map_artifact_repository.site_name(mapped_site_id),
                    count,
                )
            )
        return result

    def _warn_dropped_findspots(self, dropped_ids: frozenset[int]) -> None:
        if not dropped_ids:
            return
        with self._warning_lock:
            if dropped_ids in self._reported_dropped_ids:
                return
            if len(self._reported_dropped_ids) >= MAX_REPORTED_DROPPED_SETS:
                del self._reported_dropped_ids[next(iter(self._reported_dropped_ids))]
            self._reported_dropped_ids[dropped_ids] = None
        LOGGER.warning(
            "Map artifacts skipped findspots with missing or mismatched site metadata: %s",
            sorted(dropped_ids),
        )

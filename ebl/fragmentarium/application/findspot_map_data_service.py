from dataclasses import dataclass
from typing import Optional, Sequence

import attr

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
)
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.provenance.application.provenance_service import ProvenanceService


@dataclass(frozen=True)
class FindspotMapData:
    findspot: Findspot
    accessible_fragment_count: int


class FindspotMapDataService:
    """Serves map-data from the version-controlled, read-only findspot-to-polygon
    mapping artifacts, joined at request time against live Findspot metadata and
    authorization-filtered fragment counts. No mapLocation value is read from or
    written to MongoDB by this service."""

    def __init__(
        self,
        findspot_repository: MongoFindspotRepository,
        fragment_repository: FragmentRepository,
        provenance_service: ProvenanceService,
        map_artifact_repository: Optional[MapArtifactRepository] = None,
    ) -> None:
        self._findspot_repository = findspot_repository
        self._fragment_repository = fragment_repository
        self._provenance_service = provenance_service
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
        map_locations = self._map_artifact_repository.load_map_locations(
            (site_id,) if site_id is not None else None
        )
        if not map_locations:
            return []

        site = None if site_id is None else self._provenance_service.find_by_id(site_id)
        findspots = sorted(
            (
                attr.evolve(findspot, map_location=map_locations[findspot.id_])
                for findspot in self._findspot_repository.find_all()
                if findspot.id_ in map_locations
                and (site is None or (findspot.site and findspot.site.id == site.id))
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
        return [
            FindspotMapData(findspot, counts.get(findspot.id_, 0))
            for findspot in findspots
        ]

from dataclasses import dataclass
from typing import Optional, Sequence

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
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
    def __init__(
        self,
        findspot_repository: MongoFindspotRepository,
        fragment_repository: FragmentRepository,
        provenance_service: ProvenanceService,
    ) -> None:
        self._findspot_repository = findspot_repository
        self._fragment_repository = fragment_repository
        self._provenance_service = provenance_service

    def find_map_data(
        self,
        site_id: Optional[str] = None,
        user_scopes: Sequence[Scope] = (),
    ) -> Sequence[FindspotMapData]:
        site = None if site_id is None else self._provenance_service.find_by_id(site_id)

        findspots = sorted(
            (
                findspot
                for findspot in self._findspot_repository.find_all()
                if findspot.map_location is not None
                and (site is None or (findspot.site and findspot.site.id == site.id))
            ),
            key=lambda findspot: findspot.id_,
        )

        counts = self._fragment_repository.count_fragments_by_findspot_ids(
            [findspot.id_ for findspot in findspots], user_scopes
        )
        return [
            FindspotMapData(findspot, counts.get(findspot.id_, 0))
            for findspot in findspots
        ]

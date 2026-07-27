from falcon import Request, Response

from ebl.errors import DataError
from ebl.fragmentarium.application.findspot_map_data_schema import (
    FindspotMapDataSchema,
)
from ebl.fragmentarium.application.findspot_map_data_service import (
    FindspotMapDataService,
)
from ebl.provenance.application.provenance_service import ProvenanceService


class FindspotMapDataResource:
    def __init__(
        self,
        service: FindspotMapDataService,
        provenance_service: ProvenanceService,
    ) -> None:
        self._service = service
        self._provenance_service = provenance_service

    def _parse_site(self, site: str | None) -> str | None:
        if site is None:
            return None
        if site != site.upper():
            raise DataError("site must be the canonical provenance identifier.")
        if self._provenance_service.find_by_id(site) is None:
            raise DataError(f"Invalid site identifier: {site}")
        return site

    def on_get(self, req: Request, resp: Response) -> None:
        site_id = self._parse_site(req.get_param("site"))
        data = self._service.find_map_data(
            site_id=site_id,
            user_scopes=req.context.user.get_scopes(
                prefix="read:", suffix="-fragments"
            ),
        )
        schema = FindspotMapDataSchema(many=True)
        resp.media = {"findspots": schema.dump(data)}

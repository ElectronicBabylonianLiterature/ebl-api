from falcon import Request, Response

from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.query.parameter_parser import parse_genre
from ebl.errors import DataError
from ebl.fragmentarium.application.findspot_map_data_schema import (
    FindspotMapDataSchema,
)
from ebl.fragmentarium.application.findspot_map_data_service import (
    FindspotMapDataService,
)
from ebl.fragmentarium.domain.genres import genres
from ebl.provenance.application.provenance_service import ProvenanceService

_PERIODS = frozenset(period.long_name for period in Period)
_PERIOD_MODIFIERS = frozenset(modifier.value for modifier in PeriodModifier)


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

    @staticmethod
    def _validate_filter(value: str | None, allowed: frozenset[str], name: str):
        if value is not None and value not in allowed:
            raise DataError(f"Invalid {name}: {value}")
        return value

    def on_get(self, req: Request, resp: Response) -> None:
        site_id = self._parse_site(req.get_param("site"))
        genre = parse_genre(dict(req.params)).get("genre")
        if genre is not None and tuple(genre) not in genres:
            raise DataError(f"Invalid genre: {':'.join(genre)}")
        data = self._service.find_map_data(
            site_id=site_id,
            user_scopes=req.context.user.get_scopes(
                prefix="read:", suffix="-fragments"
            ),
            script_period=self._validate_filter(
                req.get_param("scriptPeriod"), _PERIODS, "scriptPeriod"
            ),
            script_period_modifier=self._validate_filter(
                req.get_param("scriptPeriodModifier"),
                _PERIOD_MODIFIERS,
                "scriptPeriodModifier",
            ),
            genre=genre,
        )
        schema = FindspotMapDataSchema(many=True)
        resp.media = {"findspots": schema.dump(data)}

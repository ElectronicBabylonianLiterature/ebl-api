import logging
from falcon import Request, Response
from urllib.parse import parse_qs
from ebl.errors import NotFoundError
from marshmallow import EXCLUDE

from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
)

logger = logging.getLogger(__name__)


class DossiersResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        parsed_params = parse_qs(req.query_string)
        ids = parsed_params.get("ids[]", [])
        if ids:
            try:
                dossiers = self._dossiersRepository.query_by_ids(ids)
            except ValueError as error:
                raise NotFoundError(
                    f"No dossier records matching {req.params} found."
                ) from error
        else:
            dossiers = self._dossiersRepository.find_all()

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)


class DossiersSearchResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.params.get("query", "")
        provenance = req.params.get("provenance")
        script_period = req.params.get("scriptPeriod")

        dossiers = self._dossiersRepository.search(
            query, provenance=provenance, script_period=script_period
        )

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)

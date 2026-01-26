from falcon import Request, Response
from urllib.parse import parse_qs
from ebl.errors import NotFoundError
from marshmallow import EXCLUDE

from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
)


class DossiersResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            parsed_params = parse_qs(req.query_string)
            ids = parsed_params.get("ids[]", [])
            if not ids:
                raise ValueError("No valid IDs provided in the request.")

            dossiers = self._dossiersRepository.query_by_ids(ids)
        except ValueError as error:
            raise NotFoundError(
                f"No dossier records matching {req.params} found."
            ) from error

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)


class DossiersSearchResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.get_param("query", default="")
        dossiers = self._dossiersRepository.search(query)
        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)

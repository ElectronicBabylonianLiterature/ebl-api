from falcon import Request, Response
from urllib.parse import parse_qs
from ebl.errors import NotFoundError, DataError
from marshmallow import EXCLUDE

from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
    DossierPaginationSchema,
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


class DossierSearchResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            text = req.params.get("searchText", "")
            limit = int(req.params.get("limit", 20))
            page = int(req.params.get("page", 0))
            offset = page * limit
            
            if limit < 0 or limit > 100:
                raise DataError("Limit must be between 0 and 100")
            if page < 0:
                raise DataError("Page must be non-negative")
            
            pagination = self._dossiersRepository.search(text, offset, limit)
        except ValueError as error:
            raise DataError("Invalid pagination parameters") from error

        resp.media = DossierPaginationSchema().dump(pagination)

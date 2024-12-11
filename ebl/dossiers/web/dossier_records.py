from falcon import Request, Response
from ebl.errors import NotFoundError

from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
)


class DossiersResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            dossiers = self._dossiersRepository.fetch(req.params["id"])
        except ValueError as error:
            raise NotFoundError(
                f"No dossier records matching {str(req.params)} found."
            ) from error
        resp.media = DossierRecordSchema().dump([dossiers], many=True)

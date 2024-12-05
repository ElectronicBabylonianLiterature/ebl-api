from falcon import Request, Response
from ebl.errors import NotFoundError

from ebl.dossier.application.dossier_repository import DossierRepository
from ebl.dossier.infrastructure.mongo_dossier_repository import (
    DossierRecordSchema,
)


class DossierResource:
    def __init__(self, _dossierRepository: DossierRepository):
        self._dossierRepository = _dossierRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            response = self._dossierRepository.fetch(req.params)
        except ValueError as error:
            raise NotFoundError(
                f"No dossier entries matching {str(req.params)} found."
            ) from error
        resp.media = DossierRecordSchema().dump(response, many=True)

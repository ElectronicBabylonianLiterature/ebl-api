from falcon import Request, Response
from ebl.errors import NotFoundError

from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    AfoRegisterRecordSchema,
)


class AfoRegisterResource:
    def __init__(self, afoRegisterRepository: AfoRegisterRepository):
        self._afoRegisterRepository = afoRegisterRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            response = self._afoRegisterRepository.find(req.params)
        except ValueError as error:
            raise NotFoundError(
                f"No AfO registry entries matching {str(req.params)} found."
            ) from error
        resp.media = AfoRegisterRecordSchema().dump(response)

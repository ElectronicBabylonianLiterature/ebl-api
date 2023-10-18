from falcon import Request, Response

from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository


class AfoRegisterResource:
    def __init__(self, afoRegisterRepository: AfoRegisterRepository):
        self._afoRegisterRepository = afoRegisterRepository

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = self._afoRegisterRepository.find(req.params["query"])

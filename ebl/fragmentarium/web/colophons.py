from falcon import Request, Response
from ebl.fragmentarium.application.fragment_repository import FragmentRepository


class ColophonNamesResource:
    def __init__(
        self,
        repository: FragmentRepository,
    ):
        self._repository = repository

    def on_get(self, req: Request, resp: Response):
        resp.media = self._repository.fetch_names(req.params["query"])

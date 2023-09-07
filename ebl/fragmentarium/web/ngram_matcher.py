from falcon import Request, Response
from ebl.fragmentarium.application.fragment_repository import FragmentRepository


class NgramAlignResource:
    def __init__(
        self,
        repository: FragmentRepository,
    ):
        self.fragment_repository = repository

    def on_get(self, req: Request, resp: Response, number) -> None:
        resp.media = {}

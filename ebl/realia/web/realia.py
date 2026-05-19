from falcon import Request, Response

from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.infrastructure.mongo_realia_repository import RealiaEntrySchema


class RealiaResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, _req: Request, resp: Response, realia_id: str) -> None:
        entry = self._realia_repository.find(realia_id)
        resp.media = RealiaEntrySchema().dump(entry)


class RealiaSearchResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.get_param("query", default="")
        entries = self._realia_repository.search(query)
        resp.media = RealiaEntrySchema(many=True).dump(entries)

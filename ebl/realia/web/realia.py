from falcon import HTTP_OK, HTTPMethodNotAllowed, Request, Response

from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema


class RealiaResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, _req: Request, resp: Response, realia_id: str) -> None:
        entry = self._realia_repository.find(realia_id)
        resp.media = RealiaEntrySchema().dump(entry)


class RealiaLemmaSink:
    _allowed_methods = ["GET", "OPTIONS"]

    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._resource = RealiaResource(realia_repository)

    def __call__(self, req: Request, resp: Response, realia_id: str) -> None:
        if req.method == "OPTIONS":
            resp.set_header("Allow", ", ".join(self._allowed_methods))
            resp.status = HTTP_OK
            return
        if req.method != "GET":
            raise HTTPMethodNotAllowed(self._allowed_methods)
        self._resource.on_get(req, resp, realia_id)


class RealiaByIdResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, _req: Request, resp: Response, realia_id: str) -> None:
        entry = self._realia_repository.find_by_realia_id(realia_id)
        resp.media = RealiaEntrySchema().dump(entry)


class RealiaSearchResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.get_param("query", default="")
        entries = self._realia_repository.search(query)
        resp.media = RealiaEntrySchema(many=True).dump(entries)


class RealiaListResource:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = self._realia_repository.list_all_realia()

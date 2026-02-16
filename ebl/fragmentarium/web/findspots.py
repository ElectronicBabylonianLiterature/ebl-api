from falcon import Response, Request
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema


class FindspotResource:
    def __init__(self, repository: MongoFindspotRepository):
        self._repository = repository

    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = FindspotSchema().dump(self._repository.find_all(), many=True)

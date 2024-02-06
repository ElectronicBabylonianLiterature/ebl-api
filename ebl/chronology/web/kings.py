from falcon import Request, Response

from ebl.chronology.application.kings_repository import KingsRepository
from ebl.chronology.chronology import (
    KingSchema,
)


class AllKingsResource:
    def __init__(self, kingsRepository: KingsRepository):
        self._kingsRepository = kingsRepository

    def on_get(self, req: Request, resp: Response) -> None:
        response = self._kingsRepository.list_all_kings()
        resp.media = KingSchema().dump(response, many=True)

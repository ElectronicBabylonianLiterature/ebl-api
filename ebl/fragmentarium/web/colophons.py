import falcon
from falcon import Request, Response
from ebl.fragmentarium.application.fragment_repository import FragmentRepository

from ebl.fragmentarium.application.colophon_schema import (
    ColophonSchema,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope


class ColophonResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user = req.context.user
        data = req.media["colophon"]

        updated_fragment, has_photo = self._updater.update_colophon(
            parse_museum_number(number),
            ColophonSchema().load(data),
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)


class ColophonNamesResource:
    def __init__(
        self,
        repository: FragmentRepository,
    ):
        self._repository = repository

    def on_get(self, req: Request, resp: Response):
        resp.media = self._repository.fetch_names(req.params["query"])

from typing import Sequence

import falcon  # pyre-ignore
from falcon import Response, Request

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.fragmentarium.domain.genre import genres
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.users.web.require_scope import require_scope


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @staticmethod
    def _validate_genre(genres_retrieved: Sequence[Sequence[str]]):
        return all(genre in genres for genre in genres_retrieved)

    @falcon.before(require_scope, "transliterate:fragments")
    # pyre-ignore[11]
    def on_post(self, req: Request, resp: Response, number: FragmentNumber) -> None:
        if FragmentGenreResource._validate_genre(req.media["genre"]):
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_genre(
                number, req.media["genre"], user
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        else:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                "title": resp.status,
                "description": "Not a valid Genre",
            }

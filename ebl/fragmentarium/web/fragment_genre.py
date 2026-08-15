from typing import List, cast

import falcon
from falcon import Response, Request

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.fragment import Genre
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater, dto_factory: FragmentDtoFactory):
        self._updater = updater
        self._dto_factory = dto_factory

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user: User = req.context["user"]
            updated_fragment, has_photo = self._updater.update_genres(
                parse_museum_number(number),
                cast(List[Genre], GenreSchema().load(req.media["genres"], many=True)),
                user,
            )
            resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
        except ValueError as error:
            raise DataError(error)

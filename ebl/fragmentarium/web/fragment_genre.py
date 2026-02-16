import falcon
from falcon import Response, Request

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_genres(
                parse_museum_number(number),
                GenreSchema().load(req.media["genres"], many=True),
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except ValueError as error:
            raise DataError(error)

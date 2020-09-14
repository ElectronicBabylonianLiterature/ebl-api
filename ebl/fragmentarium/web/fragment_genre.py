import falcon  # pyre-ignore[21]
from falcon import Response, Request

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    # pyre-ignore[11]
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_genre(
                parse_museum_number(number),
                req.media["genre"], user
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except ValueError as error:
            raise DataError(error)

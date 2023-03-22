import falcon
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from ebl.errors import DataError
from ebl.fragmentarium.domain.fragment import NotLowestJoinError
from marshmallow import ValidationError


class IntroductionResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_introduction(
                parse_museum_number(number),
                req.media["introduction"],
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)

        except (NotLowestJoinError, ValidationError) as error:
            raise DataError(error) from error

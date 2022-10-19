import falcon
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate
from ebl.fragmentarium.application.fragment_schema import parse_introduction

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from ebl.errors import DataError
from ebl.fragmentarium.domain.fragment import NotLowestJoinError

INTRODUCTION_DTO_SCHEMA = {
    "type": "object",
    "properties": {"introduction": {"type": "string"}},
    "required": ["introduction"],
}


class IntroductionResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(INTRODUCTION_DTO_SCHEMA)
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_introduction(
                parse_museum_number(number),
                parse_introduction(req.media["introduction"]),
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)

        except NotLowestJoinError as error:
            raise DataError(error) from error

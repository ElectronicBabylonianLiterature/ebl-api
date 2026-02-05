import falcon
from falcon import Response, Request

from ebl.errors import DataError
from marshmallow import ValidationError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema


class FragmentScriptResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_script(
                parse_museum_number(number),
                ScriptSchema().load(req.media["script"]),
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except ValidationError as error:
            raise DataError(f"Invalid script data: '{req.media['script']}'") from error

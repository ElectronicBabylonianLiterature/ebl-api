import falcon  # pyre-ignore
from falcon import Response, Request
from falcon.media.validators.jsonschema import validate

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.users.web.require_scope import require_scope

TRANSLITERATION_DTO_SCHEMA = {
    "type": "object",
    "properties": {"transliteration": {"type": "string"}, "notes": {"type": "string"},},
    "required": ["transliteration", "notes"],
}


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str):
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_genre(
                number, req.media, user
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except TransliterationError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                "title": resp.status,
                "description": str(error),
                "errors": error.errors,
            }
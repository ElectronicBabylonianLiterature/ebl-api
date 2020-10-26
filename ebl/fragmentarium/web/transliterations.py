import falcon  # pyre-ignore[21]
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate  # pyre-ignore[21]

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.line_to_vec_updater import create_line_to_vec
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.users.web.require_scope import require_scope


TRANSLITERATION_DTO_SCHEMA = {
    "type": "object",
    "properties": {"transliteration": {"type": "string"}, "notes": {"type": "string"}},
    "required": ["transliteration", "notes"],
}


class TransliterationResource:
    def __init__(self, updater: FragmentUpdater, transliteration_factory):
        self._updater = updater
        self._transliteration_factory = transliteration_factory

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(TRANSLITERATION_DTO_SCHEMA)  # pyre-ignore[56]
    # pyre-ignore[11]
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_transliteration(
                parse_museum_number(number),
                self._create_transliteration(req.media),
                user,
            )
            updated_fragment, has_photo = self._updater.update_line_to_vec(parse_museum_number(number), create_line_to_vec(updated_fragment.text.lines), user)
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except TransliterationError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                "title": resp.status,
                "description": str(error),
                "errors": error.errors,
            }

    def _create_transliteration(self, media):
        return self._transliteration_factory.create(
            Atf(media["transliteration"]), media["notes"]
        )

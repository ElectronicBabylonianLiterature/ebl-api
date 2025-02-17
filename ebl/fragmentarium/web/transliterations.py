import falcon
from falcon import Request, Response
from falcon.media.validators.jsonschema import validate

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.transliteration_error import (
    TransliterationError,
    DuplicateLabelError,
    ExtentLabelError,
)
from ebl.users.web.require_scope import require_scope
from ebl.errors import DataError
from ebl.fragmentarium.domain.fragment import NotLowestJoinError

TRANSLITERATION_DTO_SCHEMA = {
    "type": "object",
    "properties": {
        "transliteration": {"type": "string"},
        "notes": {"type": "string"},
        "introduction": {"type": "string"},
    },
    "required": ["transliteration"],
    "additionalProperties": False,
}


class TransliterationResource:
    def __init__(self, updater: FragmentUpdater, transliteration_factory):
        self._updater = updater
        self._transliteration_factory = transliteration_factory

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_transliteration(
                parse_museum_number(number),
                self._create_transliteration(req.media),
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except (
            DuplicateLabelError,
            ExtentLabelError,
            TransliterationError,
        ) as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                "title": resp.status,
                "description": str(error),
                "errors": error.errors,
            }
        except NotLowestJoinError as error:
            raise DataError(error) from error

    def _create_transliteration(self, media):
        try:
            return self._transliteration_factory.create(Atf(media["transliteration"]))
        except ValueError as error:
            raise DataError(error) from error

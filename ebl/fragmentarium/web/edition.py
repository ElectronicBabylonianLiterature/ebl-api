from typing import Optional
from falcon import Request, Response
import falcon
from falcon.media.validators.jsonschema import validate
from marshmallow import ValidationError

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.domain.fragment import NotLowestJoinError
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.transliteration_error import (
    DuplicateLabelError,
    ExtentLabelError,
    TransliterationError,
)
from ebl.users.web.require_scope import require_scope


EDITION_DTO_SCHEMA = {
    "type": "object",
    "properties": {
        "transliteration": {"type": "string"},
        "notes": {"type": "string"},
        "introduction": {"type": "string"},
    },
    "additionalProperties": False,
}


class EditionResource:
    def __init__(
        self,
        updater: FragmentUpdater,
        transliteration_factory: TransliterationUpdateFactory,
    ):
        self._updater = updater
        self._transliteration_factory = transliteration_factory

    def _create_transliteration(
        self, transliteration: Optional[str]
    ) -> Optional[TransliterationUpdate]:
        try:
            return (
                None
                if transliteration is None
                else self._transliteration_factory.create(Atf(transliteration))
            )

        except ValueError as error:
            raise DataError(error) from error

    @falcon.before(require_scope, "transliterate:fragments")
    @validate(EDITION_DTO_SCHEMA)
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user

            updated_fragment, has_photo = self._updater.update_edition(
                parse_museum_number(number),
                user,
                req.media.get("introduction"),
                req.media.get("notes"),
                self._create_transliteration(req.media.get("transliteration")),
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

        except (NotLowestJoinError, ValidationError) as error:
            raise DataError(error) from error

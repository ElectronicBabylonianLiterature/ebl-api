from typing import Union
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologyInputSchema,
    ExcavationNumberSchema,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater

import falcon
from falcon import Request, Response
from marshmallow import ValidationError
from ebl.errors import DataError
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.users.domain.user import User
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope


class ArchaeologyResource:
    def __init__(
        self, updater: FragmentUpdater, provenance_service: ProvenanceService
    ) -> None:
        self._updater = updater
        self._provenance_service = provenance_service

    def _parse_excavation_number(self, excavation_number: object) -> Union[dict, None]:
        if excavation_number is not None and not isinstance(excavation_number, str):
            raise DataError("excavationNumber must be a string or null.")
        if not excavation_number:
            return None
        document = ExcavationNumberSchema().dump(parse_museum_number(excavation_number))
        assert isinstance(document, dict)
        return document

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user: User = req.context["user"]
        payload = req.media
        if not isinstance(payload, dict) or not isinstance(
            payload.get("archaeology"), dict
        ):
            raise DataError("archaeology must be an object.")
        data = dict(payload["archaeology"])

        data["excavationNumber"] = self._parse_excavation_number(
            data.get("excavationNumber")
        )
        try:
            archaeology = ArchaeologyInputSchema(
                context={"provenance_service": self._provenance_service}
            ).load(data)
        except ValidationError as error:
            raise DataError(f"Invalid archaeology data: {error.messages}") from error
        assert isinstance(archaeology, Archaeology)
        updated_fragment, has_photo = self._updater.update_archaeology(
            parse_museum_number(number), archaeology, user
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)

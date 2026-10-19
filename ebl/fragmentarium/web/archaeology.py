from typing import Union, cast
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologyInputSchema,
    ExcavationNumberSchema,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.archaeology import Archaeology

import falcon
from falcon import Request, Response
from marshmallow import ValidationError
from ebl.errors import DataError
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope


class ArchaeologyResource:
    def __init__(
        self,
        updater: FragmentUpdater,
        provenance_service: ProvenanceService,
        dto_factory: FragmentDtoFactory,
    ) -> None:
        self._updater = updater
        self._provenance_service = provenance_service
        self._dto_factory = dto_factory

    def _parse_excavation_number(self, excavation_number: object) -> Union[dict, None]:
        if excavation_number is not None and not isinstance(excavation_number, str):
            raise DataError("excavationNumber must be a string or null.")
        return (
            None
            if not excavation_number
            else cast(
                dict,
                ExcavationNumberSchema().dump(parse_museum_number(excavation_number)),
            )
        )

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
            archaeology = cast(
                Archaeology,
                ArchaeologyInputSchema(
                    context={"provenance_service": self._provenance_service}
                ).load(data),
            )
        except ValidationError as error:
            raise DataError(f"Invalid archaeology data: {error.messages}") from error
        updated_fragment, has_photo = self._updater.update_archaeology(
            parse_museum_number(number),
            archaeology,
            user,
        )
        resp.media = self._dto_factory.create(updated_fragment, user, has_photo)

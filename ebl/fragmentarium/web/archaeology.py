from typing import Union, cast
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologySchema,
    ExcavationNumberSchema,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.archaeology import Archaeology

import falcon
from falcon import Request, Response
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

    def _parse_excavation_number(
        self, excavation_number: Union[str, None]
    ) -> Union[dict, None]:
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
        data = req.media["archaeology"]

        data["excavationNumber"] = self._parse_excavation_number(
            data.get("excavationNumber")
        )
        updated_fragment, has_photo = self._updater.update_archaeology(
            parse_museum_number(number),
            cast(
                Archaeology,
                ArchaeologySchema(
                    context={"provenance_service": self._provenance_service}
                ).load(data),
            ),
            user,
        )
        resp.media = self._dto_factory.create(updated_fragment, user, has_photo)

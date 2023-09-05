from typing import Union
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologySchema,
    ExcavationNumberSchema,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater

import falcon
from falcon import Request, Response
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope


class ArchaeologyResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    def _parse_excavation_number(
        self, excavation_number: Union[str, None]
    ) -> Union[dict, None]:
        return (
            None
            if not excavation_number
            else ExcavationNumberSchema().dump(parse_museum_number(excavation_number))
        )

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user = req.context.user
        data = req.media["archaeology"]

        data["excavationNumber"] = self._parse_excavation_number(
            data.get("excavationNumber")
        )
        updated_fragment, has_photo = self._updater.update_archaeology(
            parse_museum_number(number),
            ArchaeologySchema().load(data),
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)

from typing import List, Optional, cast

import falcon
from falcon import Response, Request

from ebl.errors import DataError
from marshmallow import ValidationError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.users.domain.user import User
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.domain.date import Date, DateSchema


class FragmentDateResource:
    def __init__(self, updater: FragmentUpdater, dto_factory: FragmentDtoFactory):
        self._updater = updater
        self._dto_factory = dto_factory

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user: User = req.context["user"]
            updated_fragment, has_photo = self._updater.update_date(
                parse_museum_number(number),
                (
                    cast(Optional[Date], DateSchema().load(req.media["date"]))
                    if "date" in req.media
                    else None
                ),
                user,
            )
            resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
        except ValidationError as error:
            raise DataError(f"Invalid date data: '{req.media['date']}'") from error


class FragmentDatesInTextResource:
    def __init__(self, updater: FragmentUpdater, dto_factory: FragmentDtoFactory):
        self._updater = updater
        self._dto_factory = dto_factory

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user: User = req.context["user"]
            updated_fragment, has_photo = self._updater.update_dates_in_text(
                parse_museum_number(number),
                cast(
                    List[Date], DateSchema().load(req.media["datesInText"], many=True)
                ),
                user,
            )
            resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
        except ValidationError as error:
            raise DataError(
                f"Invalid datesInText data: '{req.media['datesInText']}'"
            ) from error

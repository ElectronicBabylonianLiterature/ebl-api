import falcon
from falcon import Response, Request

from ebl.errors import DataError
from marshmallow import ValidationError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from ebl.fragmentarium.domain.date import DateSchema


class FragmentDateResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_date(
                parse_museum_number(number),
                DateSchema().load(req.media["date"]) if "date" in req.media else None,
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except ValidationError as error:
            raise DataError(f"Invalid date data: '{req.media['date']}'") from error


class FragmentDatesInTextResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        try:
            user = req.context.user
            updated_fragment, has_photo = self._updater.update_dates_in_text(
                parse_museum_number(number),
                DateSchema().load(req.media["datesInText"], many=True),
                user,
            )
            resp.media = create_response_dto(updated_fragment, user, has_photo)
        except ValidationError as error:
            raise DataError(
                f"Invalid datesInText data: '{req.media['datesInText']}'"
            ) from error

import falcon  # pyre-ignore
from falcon import Response, Request

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.users.web.require_scope import require_scope


class FragmentGenreResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: FragmentNumber) -> None:
        # pyre-ignore[11]
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_genre(
            number, req.media["genre"], user
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)

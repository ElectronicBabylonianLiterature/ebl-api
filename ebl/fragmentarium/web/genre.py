import falcon  # pyre-ignore[21]
from falcon import Response, Request

from ebl.fragmentarium.domain.genre import genres
from ebl.users.web.require_scope import require_scope


class GenreResource:

    @falcon.before(require_scope, "transliterate:fragments")
    def on_get(self, _req: Request, resp: Response) -> None:  # pyre-ignore[11]
        resp.media = genres

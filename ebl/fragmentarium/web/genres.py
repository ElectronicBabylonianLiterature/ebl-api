import falcon
from falcon import Response, Request

from ebl.fragmentarium.domain.genres import genres
from ebl.users.web.require_scope import require_scope


class GenresResource:

    auth = {"exempt_methods": ["GET"]}

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = genres

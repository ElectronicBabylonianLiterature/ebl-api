import falcon  # pyre-ignore[21]
from falcon import Response, Request

from ebl.fragmentarium.domain.genres import genres
from ebl.users.web.require_scope import require_scope


class GenresResource:
    @falcon.before(require_scope, "read:fragments")
    def on_get(self, _req: Request, resp: Response) -> None:  # pyre-ignore[11]
        resp.media = genres

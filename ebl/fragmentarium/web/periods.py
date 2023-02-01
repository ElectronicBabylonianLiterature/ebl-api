import falcon
from falcon import Response, Request
from ebl.common.period import Period

from ebl.users.web.require_scope import require_scope


class PeriodsResource:

    auth = {"exempt_methods": ["GET"]}

    @falcon.before(require_scope, "read:fragments")
    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = [
            period.long_name for period in Period if period is not Period.NONE
        ]

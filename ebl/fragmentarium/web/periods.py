from falcon import Response, Request
from ebl.common.domain.period import Period


class PeriodsResource:
    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = [
            period.long_name for period in Period if period is not Period.NONE
        ]

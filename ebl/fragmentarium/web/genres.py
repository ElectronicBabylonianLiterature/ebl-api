from falcon import Response, Request
from ebl.fragmentarium.domain.genres import genres


class GenresResource:
    def on_get(self, _req: Request, resp: Response) -> None:
        resp.media = genres

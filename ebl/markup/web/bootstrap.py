import falcon
from falcon import Request, Response

from ebl.context import Context
from ebl.markup.domain.converters import markup_string_to_json


class Markup:
    auth = {"auth_disabled": True}

    def on_get(self, req: Request, resp: Response) -> None:
        resp.media = markup_string_to_json(req.params["text"])


def create_markup_route(api: falcon.App, context: Context) -> None:
    api.add_route("/markup", Markup())

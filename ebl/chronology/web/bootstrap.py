import falcon
from ebl.context import Context
from ebl.chronology.web.kings import AllKingsResource


def create_afo_register_routes(api: falcon.App, context: Context):
    all_kings = AllKingsResource(context.kings_repository)
    api.add_route("/kings-all", all_kings)

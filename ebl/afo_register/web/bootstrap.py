import falcon
from ebl.context import Context

from ebl.afo_register.web.afo_register_entries import AfoRegisterResource


def create_afo_register_routes(api: falcon.App, context: Context):
    afo_register_search = AfoRegisterResource(context.afo_register_repository)
    api.add_route("/afo-register", afo_register_search)

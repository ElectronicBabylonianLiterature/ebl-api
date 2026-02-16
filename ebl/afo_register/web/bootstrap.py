import falcon
from ebl.context import Context

from ebl.afo_register.web.afo_register_records import (
    AfoRegisterResource,
    AfoRegisterTextsAndNumbersResource,
    AfoRegisterSuggestionsResource,
)


def create_afo_register_routes(api: falcon.App, context: Context):
    afo_register_search = AfoRegisterResource(context.afo_register_repository)
    afo_register_search_texts_and_numbers = AfoRegisterTextsAndNumbersResource(
        context.afo_register_repository
    )
    afo_register_suggestions_search = AfoRegisterSuggestionsResource(
        context.afo_register_repository
    )
    api.add_route("/afo-register", afo_register_search)
    api.add_route("/afo-register/texts-numbers", afo_register_search_texts_and_numbers)
    api.add_route("/afo-register/suggestions", afo_register_suggestions_search)

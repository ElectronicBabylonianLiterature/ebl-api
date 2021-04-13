import falcon

from ebl.context import Context
from ebl.signs.web.sign_search import SignsSearch

from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


def create_signs_routes(api: falcon.API, context: Context, spec):
    signs = MemoizingSignRepository(context.sign_repository)
    signs_search = SignsSearch(signs)
    api.add_route("/signs", signs_search)
    spec.path(resource=signs_search)

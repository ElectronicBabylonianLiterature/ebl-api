import falcon
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.users.domain.user import User


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    user: User = req.context.user

    if not user.has_scope(Scope.from_string(scope)):
        raise falcon.HTTPForbidden()


def require_folio_scope(req: falcon.Request, _resp, _resource, params):
    user: User = req.context.user

    if not user.can_read_folio(
        params["name"] if "name" in params else params["folio_name"]
    ):
        raise falcon.HTTPForbidden()


def require_fragment_read_scope(req: falcon.Request, _resp, resource, params):
    user: User = req.context.user

    if fragment_scopes := resource._finder.fetch_scopes(
        parse_museum_number(params["number"])
    ):
        if not user.can_read_fragment(fragment_scopes):
            raise falcon.HTTPForbidden()

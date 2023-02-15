import falcon
from ebl.fragmentarium.web.dtos import parse_museum_number


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    if not req.context.user.has_scope(scope):
        raise falcon.HTTPForbidden()


def require_folio_scope(req: falcon.Request, _resp, _resource, params):
    scope = (
        f"read:{params['name'] if 'name' in params else params['folio_name']}-folios"
    )

    if not req.context.user.can_read_folio(scope):
        raise falcon.HTTPForbidden()


def require_fragment_scope(req: falcon.Request, _resp, resource, params):
    if fragment_scopes := resource._finder.fetch_scopes(
        parse_museum_number(params["number"])
    ):
        if not req.context.user.can_read_fragment(fragment_scopes):
            raise falcon.HTTPForbidden()

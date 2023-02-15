import falcon
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.common.folios import HIDDEN_SCOPES


def has_scope(req: falcon.Request, scope: str) -> bool:
    user = getattr(req.context, "user", None)

    return (
        user.has_scope(scope)
        if user
        else scope.startswith("read:") and scope not in HIDDEN_SCOPES
    )


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    if not has_scope(req, scope):
        raise falcon.HTTPForbidden()


def require_folio_scope(req: falcon.Request, _resp, _resource, params):
    scope = (
        f"read:{params['name'] if 'name' in params else params['folio_name']}-folios"
    )

    if scope in HIDDEN_SCOPES and not has_scope(req, scope):
        raise falcon.HTTPForbidden()


def require_fragment_scope(req: falcon.Request, _resp, resource, params):
    if fragment_scopes := resource._finder.fetch_scopes(
        parse_museum_number(params["number"])
    ):
        if not any(
            has_scope(req, f"read:{scope}-fragments") for scope in fragment_scopes
        ):
            raise falcon.HTTPForbidden()

import falcon

from ebl.fragmentarium.web.dtos import parse_museum_number

HIDDEN_SCOPES = [
    "read:ILF-folios",
    "read:SP-folios",
    "read:USK-folios",
    "read:ARG-folios",
    "read:WRM-folios",
    "read:MJG-folios",
    "read:SP-folios",
    "read:UG-folios",
    "read:SJL-folios",
    "read:EVW-folios",
]


def has_scope(req: falcon.Request, scope: str) -> bool:
    if not hasattr(req.context, "user") or not req.context.user:
        return "read:" in scope or scope in {"access:beta"}
    return req.context.user.has_scope(scope)


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
        if not all(
            has_scope(req, f"read:{scope}-fragments") for scope in fragment_scopes
        ):
            raise falcon.HTTPForbidden()

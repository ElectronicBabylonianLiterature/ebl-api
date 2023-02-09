import falcon

from ebl.fragmentarium.web.dtos import parse_museum_number


OPEN_SCOPES = [
    "read:WGL-folios",
    "read:FWG-folios",
    "read:EL-folios",
    "read:AKG-folios",
    "read:CB-folios",
    "read:JS-folios",
    "read:RB-folios",
    "read:ER-folios",
    "read:GS-folios",
]


def is_guest_session(req: falcon.Request) -> bool:
    return getattr(req.context, "user", None) is None


def has_scope(req: falcon.Request, scope: str) -> bool:
    if scope in OPEN_SCOPES:
        return True
    elif is_guest_session(req):
        return False
    else:
        return req.context.user.has_scope(scope)


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    if not has_scope(req, scope):
        raise falcon.HTTPForbidden()


def require_folio_scope(req: falcon.Request, _resp, _resource, params):
    scope = (
        f"read:{params['name'] if 'name' in params else params['folio_name']}-folios"
    )

    if scope not in OPEN_SCOPES:
        if is_guest_session(req) or not has_scope(req, scope):
            raise falcon.HTTPForbidden()


def require_fragment_scope(req: falcon.Request, _resp, resource, params):
    fragment_scopes = resource._finder.fetch_scopes(
        parse_museum_number(params["number"])
    )

    if fragment_scopes:
        if is_guest_session(req):
            raise falcon.HTTPForbidden()
        elif not all(
            has_scope(req, f"read:{scope}-fragments") for scope in fragment_scopes
        ):
            raise falcon.HTTPForbidden()

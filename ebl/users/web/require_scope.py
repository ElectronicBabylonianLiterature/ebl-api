import falcon


OPEN_FOLIO_SCOPES = [
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
    if is_guest_session(req):
        return "read:" in scope or scope == "access:beta"
    return req.context.user.has_scope(scope)


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    if not has_scope(req, scope):
        raise falcon.HTTPForbidden()


def require_folio_scope(req: falcon.Request, _resp, _resource, params):
    scope = f"read:{params['name']}-folios"

    if scope not in OPEN_FOLIO_SCOPES:
        if is_guest_session(req) or not has_scope(req, scope):
            raise falcon.HTTPForbidden()


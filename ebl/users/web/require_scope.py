import falcon


def has_scope(req: falcon.Request, scope: str) -> bool:
    if not hasattr(req.context, "user") or not req.context.user:
        return True if "read:" in scope or scope in ["access:beta"] else False
    return req.context.user.has_scope(scope)


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    if not has_scope(req, scope):
        raise falcon.HTTPForbidden()

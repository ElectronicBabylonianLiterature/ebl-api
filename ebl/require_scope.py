import falcon


def require_scope(req, _resp, _resource, scope):
    if not req.context['user'].has_scope(scope):
        raise falcon.HTTPForbidden()

import falcon


def require_scope(req, _resp, _resource, scope):
    if scope not in req.context['user']['scope']:
        raise falcon.HTTPForbidden()

import falcon
from falcon import Request

from ebl.users.domain.user import User


def require_scope(req: Request, _resp, _resource, _params, scope: str):
    user: User = req.context.user
    if not user.has_scope(scope):
        raise falcon.HTTPForbidden()

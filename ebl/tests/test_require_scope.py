import falcon
from falcon_auth import FalconAuthMiddleware, NoneAuthBackend

from ebl.auth0 import Auth0User
from ebl.require_scope import require_scope

SCOPE = 'write:words'


@falcon.before(require_scope, SCOPE)
class TestResource:
    # pylint: disable=R0903
    # pylint: disable=R0201
    def on_get(self, _req, resp):
        resp.status = falcon.HTTP_OK


def do_get(scope):
    def user_loader():
        return Auth0User(
            {
                'scope': scope
            },
            lambda: {}
        )

    auth_backend = NoneAuthBackend(user_loader)
    auth_middleware = FalconAuthMiddleware(auth_backend)
    api = falcon.API(middleware=[auth_middleware])
    api.add_route('/test', TestResource())
    client = falcon.testing.TestClient(api)

    return client.simulate_get('/test')


def test_require_scope_present():
    result = do_get([SCOPE])

    assert result.status == falcon.HTTP_OK


def test_require_scope_not_present():
    result = do_get([])

    assert result.status == falcon.HTTP_FORBIDDEN

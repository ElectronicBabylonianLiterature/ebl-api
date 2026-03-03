import falcon
from falcon import testing
from falcon_auth import FalconAuthMiddleware, NoneAuthBackend

from ebl.users.infrastructure.auth0 import Auth0User
from ebl.users.web.require_scope import require_scope

SCOPE = "write:words"


@falcon.before(require_scope, SCOPE)
class TestResource:
    def on_get(self, _req, resp):
        resp.status = falcon.HTTP_OK


def do_get(scope: str):
    def user_loader():
        return Auth0User({"scope": scope}, lambda: {})

    auth_backend = NoneAuthBackend(user_loader)
    auth_middleware = FalconAuthMiddleware(auth_backend)
    api = falcon.App(middleware=[auth_middleware])
    api.add_route("/test", TestResource())
    client = testing.TestClient(api)

    return client.simulate_get("/test")


def do_get_with_access_token(access_token: dict):
    def user_loader():
        return Auth0User(access_token, lambda: {})

    auth_backend = NoneAuthBackend(user_loader)
    auth_middleware = FalconAuthMiddleware(auth_backend)
    api = falcon.App(middleware=[auth_middleware])
    api.add_route("/test", TestResource())
    client = testing.TestClient(api)

    return client.simulate_get("/test")


def test_require_scope_present():
    result = do_get(SCOPE)

    assert result.status == falcon.HTTP_OK


def test_require_scope_not_present():
    result = do_get("")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_require_scope_present_in_permissions_only_token():
    result = do_get_with_access_token(
        {
            "scope": "openid profile offline_access",
            "permissions": [SCOPE],
        }
    )

    assert result.status == falcon.HTTP_OK


def test_require_scope_forbids_when_permissions_claim_is_not_array():
    result = do_get_with_access_token(
        {
            "scope": "openid profile offline_access",
            "permissions": SCOPE,
        }
    )

    assert result.status == falcon.HTTP_FORBIDDEN

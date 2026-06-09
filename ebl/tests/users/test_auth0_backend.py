import datetime
from typing import Any, Dict, Optional, Tuple

import falcon
from falcon import testing
from falcon.testing.client import _ResultBase
from falcon_auth import FalconAuthMiddleware
import jwt
from Cryptodome.PublicKey import RSA

from unittest.mock import Mock, patch

from ebl.users.infrastructure.auth0 import Auth0Backend


class OkResource:
    def on_get(self, _req: falcon.Request, resp: falcon.Response) -> None:
        resp.status = falcon.HTTP_OK


class ProfileCapturingResource:
    def __init__(self) -> None:
        self.captured_profile: Optional[Dict[str, Any]] = None

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        self.captured_profile = req.context.user.profile
        resp.status = falcon.HTTP_OK


def create_key_pair() -> Tuple[bytes, bytes]:
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()


def create_token(
    private_key: bytes,
    audience: str,
    issuer: str,
    overrides: Optional[Dict[str, Any]] = None,
    expires_in_seconds: int = 300,
) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload: Dict[str, Any] = {
        "sub": "user",
        "aud": audience,
        "iss": issuer,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=expires_in_seconds),
        "scope": "read:texts",
    }

    if overrides:
        for key, value in overrides.items():
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value

    return jwt.encode(payload, private_key, algorithm="RS256")


def create_client(auth_backend: Auth0Backend) -> testing.TestClient:
    auth_middleware = FalconAuthMiddleware(auth_backend)
    api = falcon.App(middleware=[auth_middleware])
    api.add_route("/test", OkResource())
    return testing.TestClient(api)


def simulate_get(auth_backend: Auth0Backend, token: Optional[str]) -> _ResultBase:
    client = create_client(auth_backend)
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return client.simulate_get("/test", headers=headers)


def create_profile_capturing_client(
    auth_backend: Auth0Backend,
) -> Tuple[testing.TestClient, ProfileCapturingResource]:
    resource = ProfileCapturingResource()
    auth_middleware = FalconAuthMiddleware(auth_backend)
    api = falcon.App(middleware=[auth_middleware])
    api.add_route("/test", resource)
    return testing.TestClient(api), resource


def test_auth_backend_valid_token() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(private_key, "test-audience", "https://issuer/")

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_OK


def test_auth_backend_missing_authorization() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    _ = private_key

    result = simulate_get(auth_backend, None)

    assert result.status == falcon.HTTP_UNAUTHORIZED


def test_auth_backend_malformed_token() -> None:
    _private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )

    result = simulate_get(auth_backend, "not-a-token")

    assert result.status == falcon.HTTP_UNAUTHORIZED


def test_auth_backend_missing_audience() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(
        private_key,
        "test-audience",
        "https://issuer/",
        overrides={"aud": None},
    )

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_UNAUTHORIZED


def test_auth_backend_invalid_issuer() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(
        private_key,
        "test-audience",
        "https://issuer/",
        overrides={"iss": "https://other/"},
    )

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_UNAUTHORIZED


def test_auth_backend_expired_token() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(
        private_key, "test-audience", "https://issuer/", expires_in_seconds=-10
    )

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_UNAUTHORIZED


def test_auth_backend_m2m_token() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(
        private_key,
        "test-audience",
        "https://issuer/",
        overrides={
            "gty": "client-credentials",
            "scope": "write:bibliography read:bibliography",
        },
    )

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_OK


def test_auth_backend_m2m_token_profile() -> None:
    private_key, public_key = create_key_pair()
    set_user = Mock()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", set_user
    )
    sub = "m2m-client-id"
    token = create_token(
        private_key,
        "test-audience",
        "https://issuer/",
        overrides={
            "sub": sub,
            "gty": "client-credentials",
            "scope": "write:bibliography read:bibliography",
        },
    )
    client, resource = create_profile_capturing_client(auth_backend)

    with patch("ebl.users.infrastructure.auth0.fetch_user_profile") as mock_fetch:
        result = client.simulate_get(
            "/test", headers={"Authorization": f"Bearer {token}"}
        )
        mock_fetch.assert_not_called()

    assert result.status == falcon.HTTP_OK
    set_user.assert_called_once_with(sub)
    assert resource.captured_profile == {"name": sub}


def test_auth_backend_non_m2m_profile_calls_userinfo() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    mock_profile = {"name": "john"}
    token = create_token(private_key, "test-audience", "https://issuer/")
    client, resource = create_profile_capturing_client(auth_backend)

    with patch("ebl.users.infrastructure.auth0.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_profile
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = client.simulate_get(
            "/test", headers={"Authorization": f"Bearer {token}"}
        )

    assert result.status == falcon.HTTP_OK
    mock_get.assert_called_once()
    assert resource.captured_profile == mock_profile


def test_auth_backend_missing_sub_is_unauthorized() -> None:
    private_key, public_key = create_key_pair()
    auth_backend = Auth0Backend(
        public_key, "test-audience", "https://issuer/", lambda _id: None
    )
    token = create_token(
        private_key,
        "test-audience",
        "https://issuer/",
        overrides={"sub": None},
    )

    result = simulate_get(auth_backend, token)

    assert result.status == falcon.HTTP_UNAUTHORIZED

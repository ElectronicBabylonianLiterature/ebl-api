import copy
from typing import Any, Callable, List, Optional

import pydash
import requests
from falcon_auth import JWTAuthBackend
from ebl.common.domain.scopes import Scope

from ebl.users.domain.user import User


def fetch_user_profile(issuer: str, authorization: str):
    url = f"{issuer}userinfo"
    headers = {"Authorization": authorization}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


class Auth0User(User):
    def __init__(self, access_token: dict, profile_factory: Callable[[], Any]):
        self._access_token = copy.deepcopy(access_token)
        self._profile_factory = pydash.once(profile_factory)

    @property
    def profile(self):
        return copy.deepcopy(self._profile_factory())

    @property
    def ebl_name(self):
        profile = self.profile
        return profile.get("https://ebabylon.org/eblName", profile["name"])

    def get_scopes(
        self, prefix: Optional[str] = "", suffix: Optional[str] = ""
    ) -> List[Scope]:
        scopes = []

        for scope in self._access_token["scope"].split():
            if scope.startswith(prefix) and scope.endswith(suffix):
                try:
                    scopes.append(Scope.from_string(scope))
                except ValueError:
                    pass

        return scopes

    def has_scope(self, scope: Scope):
        return scope.is_open or scope in self.get_scopes()


class Auth0Backend(JWTAuthBackend):
    def __init__(self, public_key, audience, issuer, set_user):
        super().__init__(
            lambda payload: payload,
            public_key,
            algorithm="RS256",
            auth_header_prefix="Bearer",
            audience=audience,
            issuer=issuer,
            verify_claims=["signature", "exp", "iat"],
            required_claims=["exp", "iat", "openid"],
        )
        self._set_user = set_user

    def authenticate(self, req, resp, resource):
        access_token = super().authenticate(req, resp, resource)
        self._set_user(access_token["sub"])
        return Auth0User(
            access_token, lambda: fetch_user_profile(self.issuer, req.auth)
        )

import copy

import pydash
import requests
from falcon_auth import JWTAuthBackend
from sentry_sdk import configure_scope


def fetch_user_profile(issuer, authorization):
    url = f'{issuer}userinfo'
    headers = {'Authorization': authorization}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def set_sentry_user(id_):
    with configure_scope() as scope:
        scope.user = {'id': id_}


class Guest:
    # pylint: disable=R0201

    @property
    def profile(self):
        return {'name': 'Guest'}

    @property
    def ebl_name(self):
        return 'Guest'

    def has_scope(self, _):
        return False

    def can_read_folio(self, _):
        return False


class Auth0User:

    def __init__(self, access_token, profile_factory):
        self._access_token = copy.deepcopy(access_token)
        self._profile_factory = pydash.once(profile_factory)

    @property
    def profile(self):
        return copy.deepcopy(self._profile_factory())

    @property
    def ebl_name(self):
        profile = self.profile
        return profile.get(
            'https://ebabylon.org/eblName',
            profile['name']
        )

    def has_scope(self, scope):
        return scope in self._access_token['scope']

    def can_read_folio(self, name):
        scope = f'read:{name}-folios'
        return self.has_scope(scope)


class Auth0Backend(JWTAuthBackend):

    def __init__(self, public_key, audience, issuer, set_user=set_sentry_user):
        super().__init__(
            lambda payload: payload,
            public_key,
            algorithm='RS256',
            auth_header_prefix='Bearer',
            audience=audience,
            issuer=issuer,
            verify_claims=['signature', 'exp', 'iat'],
            required_claims=['exp', 'iat', 'openid']
        )
        self._set_user = set_user

    def authenticate(self, req, resp, resource):
        access_token = super().authenticate(req, resp, resource)
        self._set_user(access_token['sub'])
        return Auth0User(
            access_token,
            lambda: fetch_user_profile(self.issuer, req.auth)
        )

import copy
import requests
from falcon_auth import JWTAuthBackend


def fetch_user_profile(issuer, authorization):
    url = f'{issuer}userinfo'
    headers = {'Authorization': authorization}
    return requests.get(url, headers=headers).json()


class Auth0User:

    def __init__(self, access_token, profile):
        self._access_token = copy.deepcopy(access_token)
        self._profile = copy.deepcopy(profile)

    @property
    def profile(self):
        return copy.deepcopy(self._profile)

    @property
    def ebl_name(self):
        return self._profile.get(
            'https://ebabylon.org/eblName',
            self._profile['name']
        )

    def has_scope(self, scope):
        return scope in self._access_token['scope']

    def can_read_folio(self, name):
        scope = f'read:{name}-folios'
        return self.has_scope(scope)


class Auth0Backend(JWTAuthBackend):

    def __init__(self, public_key, audience, issuer):
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

    def authenticate(self, req, resp, resource):
        access_token = super().authenticate(req, resp, resource)
        profile = fetch_user_profile(self.issuer, req.auth)
        return Auth0User(access_token, profile)



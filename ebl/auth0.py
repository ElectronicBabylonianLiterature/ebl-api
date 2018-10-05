from base64 import b64decode
import os
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from falcon_auth import JWTAuthBackend


class Auth0User:

    def __init__(self, access_token, profile):
        self._access_token = access_token
        self.profile = profile

    def has_scope(self, scope):
        return scope in self._access_token['scope']

    @property
    def ebl_name(self):
        return self.profile.get(
            'https://ebabylon.org/eblName',
            self.profile['name']
        )


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
        profile = self._fetch_user_profile(req)
        return Auth0User(access_token, profile)

    def _fetch_user_profile(self, req):
        url = f'{self.issuer}userinfo'
        headers = {'Authorization': req.get_header('Authorization', True)}
        return requests.get(url, headers=headers).json()


def create_auth0_backend():
    certificate = b64decode(os.environ['AUTH0_PEM'])
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    public_key = cert_obj.public_key()

    return Auth0Backend(
        public_key,
        os.environ['AUTH0_AUDIENCE'],
        os.environ['AUTH0_ISSUER']
    )


def fetch_auth0_user_profile(req):
    issuer = os.environ['AUTH0_ISSUER']
    url = f'{issuer}userinfo'
    headers = {'Authorization': req.get_header('Authorization', True)}
    return requests.get(url, headers=headers).json()

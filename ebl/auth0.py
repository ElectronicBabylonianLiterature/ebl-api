from base64 import b64decode
import os
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from falcon_auth import JWTAuthBackend


def auth0_user_loader(token):
    return token


def create_auth0_backend():
    certificate = b64decode(os.environ['AUTH0_PEM'])
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    public_key = cert_obj.public_key()

    return JWTAuthBackend(
        auth0_user_loader,
        public_key,
        algorithm='RS256',
        auth_header_prefix='Bearer',
        audience=os.environ['AUTH0_AUDIENCE'],
        issuer=os.environ['AUTH0_ISSUER'],
        verify_claims=['signature', 'exp', 'iat'],
        required_claims=['exp', 'iat', 'openid']
    )


def fetch_auth0_user_profile(req):
    issuer = os.environ['AUTH0_ISSUER']
    url = f'{issuer}userinfo'
    headers = {'Authorization': req.get_header('Authorization', True)}
    return requests.get(url, headers=headers).json()

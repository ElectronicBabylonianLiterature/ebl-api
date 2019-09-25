import falcon
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from falcon_apispec import FalconPlugin


API_VERSION = '0.0.1'


def create_spec(api: falcon.API, issuer: str, audience: str) -> APISpec:
    spec = APISpec(
        title="Electronic Babylonian Literature",
        version=API_VERSION,
        openapi_version='3.0.0',
        plugins=[FalconPlugin(api), MarshmallowPlugin()],
    )
    authorization_url = (
        f'{issuer}authorize'
        f'?audience={audience}'
    )
    auth0_scheme = {
        'type': "oauth2",
        'flows': {
            'implicit': {
                'authorizationUrl': authorization_url,
                'scopes': {
                    'openid': '',
                    'profile': '',
                    'read:words': '',
                    'write:words': '',
                    'read:fragments': '',
                    'transliterate:fragments': '',
                    'read:MJG-folios': '',
                    'read:WGL-folios': '',
                    'read:FWG-folios': '',
                    'read:EL-folios': '',
                    'read:AKG-folios': '',
                    'lemmatize:fragments': '',
                    'access:beta': '',
                    'read:bibliography': '',
                    'write:bibliography': '',
                    'read:WRM-folios': '',
                    'read:texts': '',
                    'write:texts': '',
                    'create:texts': '',
                    'read:CB-folios': '',
                    'read:JS-folios': '',
                }
            }
        }
    }

    spec.components.security_scheme("auth0", auth0_scheme)

    return spec

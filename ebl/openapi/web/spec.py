import falcon  # pyre-ignore[21]
from apispec import APISpec  # pyre-ignore[21]
from apispec.ext.marshmallow import MarshmallowPlugin  # pyre-ignore[21]
from falcon_apispec import FalconPlugin  # pyre-ignore[21]


API_VERSION = "0.0.6"


def create_spec(
    api: falcon.API, issuer: str, audience: str  # pyre-ignore[11]
) -> APISpec:  # pyre-ignore[11]
    spec = APISpec(
        title="Electronic Babylonian Literature",
        version=API_VERSION,
        openapi_version="3.0.0",
        plugins=[FalconPlugin(api), MarshmallowPlugin()],
        servers=[
            {"url": "http://localhost:8000", "description": "Local development server"},
            {"url": "https://api.ebabylon.org", "description": "Production server"},
        ],
    )
    authorization_url = f"{issuer}authorize" f"?audience={audience}"
    auth0_scheme = {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": authorization_url,
                "scopes": {
                    "openid": "",
                    "profile": "",
                    "read:words": "",
                    "write:words": "",
                    "read:fragments": "",
                    "transliterate:fragments": "",
                    "annotate:fragments": "",
                    "read:MJG-folios": "",
                    "read:WGL-folios": "",
                    "read:FWG-folios": "",
                    "read:EL-folios": "",
                    "read:AKG-folios": "",
                    "read:WRM-folios": "",
                    "read:CB-folios": "",
                    "read:JS-folios": "",
                    "read:ARG-folios": "",
                    "lemmatize:fragments": "",
                    "access:beta": "",
                    "read:bibliography": "",
                    "write:bibliography": "",
                    "read:texts": "",
                    "write:texts": "",
                    "create:texts": "",
                },
            }
        },
    }

    spec.components.security_scheme("auth0", auth0_scheme)
    return spec

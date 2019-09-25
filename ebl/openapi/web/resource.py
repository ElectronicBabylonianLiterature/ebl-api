import falcon
from apispec import APISpec


class OpenApiResource:
    auth = {'auth_disabled': True}

    def __init__(self, spec: APISpec):
        self._spec = spec

    def on_get(self, _req, resp):
        resp.content_type = falcon.MEDIA_YAML
        resp.body = self._spec.to_yaml()

import falcon  # pyre-ignore
from apispec import APISpec  # pyre-ignore


class OpenApiResource:
    auth = {"auth_disabled": True}

    def __init__(self, spec: APISpec):  # pyre-ignore[11]
        self._spec = spec

    def on_get(self, _req, resp):
        resp.content_type = falcon.MEDIA_YAML
        resp.body = self._spec.to_yaml()

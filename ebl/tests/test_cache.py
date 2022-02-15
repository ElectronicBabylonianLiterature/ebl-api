import falcon
from falcon import testing

from ebl.cache import cache_control


DIRECTIVES = ["public", "max-age=600"]
PATH = "/test"


class TestResource:
    @cache_control(DIRECTIVES)
    def on_get(self, _req, resp):
        resp.status = falcon.HTTP_OK


def test_cache_control():
    api = falcon.App()
    api.add_route(PATH, TestResource())
    client = testing.TestClient(api)

    result = client.simulate_get(PATH)

    assert result.headers["Cache-Control"] == ", ".join(DIRECTIVES)

import falcon
from falcon import testing

from ebl.cache.application.cache import cache_control


DIRECTIVES = ["public", "max-age=600"]
PATH = "/test"


class TestResource:
    @cache_control(DIRECTIVES)
    def on_get(self, _req, resp):
        resp.status = falcon.HTTP_OK


class TestResourceWhen:
    @cache_control(DIRECTIVES, lambda _req, _resp: False)
    def on_get(self, _req, resp):
        resp.status = falcon.HTTP_OK


def do_get(resource):
    api = falcon.App()
    api.add_route(PATH, resource)
    client = testing.TestClient(api)

    return client.simulate_get(PATH)


def test_cache_control():
    result = do_get(TestResource())

    assert result.headers["Cache-Control"] == ", ".join(DIRECTIVES)


def test_cache_control_when():
    result = do_get(TestResourceWhen())

    assert "Cache-Control" not in result.headers

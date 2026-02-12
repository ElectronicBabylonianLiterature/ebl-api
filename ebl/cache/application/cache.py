import json
import os
from typing import Callable, Sequence

from falcon import after, Request, Response
from falcon_caching import Cache


DEFAULT_TIMEOUT: int = 600
DAILY_TIMEOUT: int = 86400
CONFIG_ENVIRONMENT_VARIABLE: str = "CACHE_CONFIG"
DEFAULT_CONFIG: str = '{"CACHE_TYPE": "null"}'


def load_config() -> dict:
    return json.loads(os.environ.get(CONFIG_ENVIRONMENT_VARIABLE, DEFAULT_CONFIG))


def create_cache() -> Cache:
    return Cache(config=load_config())


def cache_control(
    directives: Sequence[str],
    when: Callable[[Request, Response], bool] = lambda _req, _resp: True,
):
    def add_header(req, resp, _resource):
        if when(req, resp):
            resp.cache_control = directives

    return after(add_header)

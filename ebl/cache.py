from functools import wraps
import json
import os
from typing import Sequence

from falcon_caching import Cache


DEFAULT_TIMEOUT: int = 600
CONFIG_ENVIRONMENT_VARIABLE: str = "CACHE_CONFIG"
DEFAULT_CONFIG: str = '{"CACHE_TYPE": "null"}'


def load_config() -> dict:
    return json.loads(os.environ.get(CONFIG_ENVIRONMENT_VARIABLE, DEFAULT_CONFIG))


def create_cache() -> Cache:
    return Cache(config=load_config())


def cache_control(directives: Sequence[str]):
    def decorator(function):
        @wraps(function)
        def wrapper(self, req, resp, *args, **kwargs):
            result = function(self, req, resp, *args, **kwargs)

            resp.cache_control = directives

            return result

        return wrapper

    return decorator

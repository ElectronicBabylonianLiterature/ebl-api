from typing import cast

from falcon import testing


def get(client: testing.TestClient, path: str) -> testing.Result:
    return cast(testing.Result, client.simulate_get(path))


def body(result: testing.Result) -> dict:
    return cast(dict, result.json)

from falcon import testing


def get(client: testing.TestClient, path: str) -> testing.Result:
    result = client.simulate_get(path)
    assert isinstance(result, testing.Result)
    return result


def body(result: testing.Result) -> dict:
    document = result.json
    assert isinstance(document, dict)
    return document

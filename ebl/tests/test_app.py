from bson.objectid import ObjectId  # pyre-ignore


def test_cors(client):
    object_id = str(ObjectId())
    headers = {"Access-Control-Request-Method": "GET"}
    result = client.simulate_options(f"/words/{object_id}", headers=headers)

    assert result.headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.headers["Access-Control-Max-Age"] == "86400"

import falcon  # pyre-ignore


def test_get_photo(client, photo):
    number = "K.1"
    result = client.simulate_get(f"/fragments/{number}/photo")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == photo.content_type
    assert result.content == photo.data
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_photo_not_found(client):
    number = "unknown"
    result = client.simulate_get(f"/fragments/{number}/photo")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_photo_not_allowed(guest_client):
    number = "K.1"
    result = guest_client.simulate_get(f"/fragments/{number}/photo")

    assert result.status == falcon.HTTP_FORBIDDEN

import falcon


def test_get_image(client, file):
    result = client.simulate_get(f"/images/{file.filename}")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == file.content_type
    assert result.content == file.data


def test_get_image_not_found(client):
    result = client.simulate_get("/images/unknown.jpg")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_image_as_guest(guest_client, file):
    result = guest_client.simulate_get(f"/images/{file.filename}")

    assert result.content == file.data

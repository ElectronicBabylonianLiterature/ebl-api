import falcon


def test_get_image(client, file):
    result = client.simulate_get(f'/images/{file.filename}')

    assert result.status == falcon.HTTP_OK
    assert result.headers['Content-Type'] == file.content_type
    assert result.content == file.data
    assert result.headers['Access-Control-Allow-Origin'] == '*'


def test_get_image_not_found(client):
    result = client.simulate_get(f'/images/unknown.jpg')

    assert result.status == falcon.HTTP_NOT_FOUND

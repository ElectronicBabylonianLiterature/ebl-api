import falcon


def test_get_folio(client, folio_with_allowed_scope):
    result = client.simulate_get("/folios/WGL/001")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == folio_with_allowed_scope.content_type
    assert result.content == folio_with_allowed_scope.data


def test_get_folio_name_not_found(client):
    result = client.simulate_get("/folios/UNKWN/001")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_folio_number_not_found(client):
    result = client.simulate_get("/folios/WGL/002")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_restricted_folio_as_guest(guest_client, folio_with_restricted_scope):
    name, number = folio_with_restricted_scope.filename[:-4].split("_")
    result = guest_client.simulate_get(f"/folios/{name}/{number}")

    assert result.status == falcon.HTTP_FORBIDDEN

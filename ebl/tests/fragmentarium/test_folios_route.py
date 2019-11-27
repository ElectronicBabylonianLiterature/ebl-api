import falcon


def test_get_folio(client, folio_with_allowed_scope):
    result = client.simulate_get(f"/folios/WGL/001")

    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == folio_with_allowed_scope.content_type
    assert result.content == folio_with_allowed_scope.data
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_get_folio_no_access(client, folio_with_restricted_scope):
    result = client.simulate_get(f"/folios/AKG/001")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_get_folio_name_not_found(client):
    result = client.simulate_get(f"/folios/UNKWN/001")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_get_folio_number_not_found(client):
    result = client.simulate_get(f"/folios/WGL/002")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_guest_scope(guest_client, folio_with_allowed_scope):
    result = guest_client.simulate_get(f"/folios/WGL/001")

    assert result.status == falcon.HTTP_FORBIDDEN

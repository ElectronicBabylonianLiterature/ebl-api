from urllib.parse import quote

import falcon

ERASURE_LINE = "°nu : ši\\ku°"


def test_get_unicode_from_a_valid_transliteration(client) -> None:
    result = client.simulate_get("/signs/transliteration/ku-nu-szi")

    assert result.status == falcon.HTTP_OK
    assert isinstance(result.json, list)


def test_unparsable_transliteration_is_unprocessable(client) -> None:
    result = client.simulate_get("/signs/transliteration/$$$")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Invalid transliteration" in result.json["description"]


def test_erasure_transliteration_is_not_a_server_error(client) -> None:
    result = client.simulate_get(
        f"/signs/transliteration/{quote(ERASURE_LINE, safe='')}"
    )

    assert result.status == falcon.HTTP_OK
    assert isinstance(result.json, list)

import falcon


def test_get_unicode_from_a_valid_transliteration(client) -> None:
    result = client.simulate_get("/signs/transliteration/ku-nu-szi")

    assert result.status == falcon.HTTP_OK
    assert isinstance(result.json, list)


def test_unparsable_transliteration_is_unprocessable(client) -> None:
    result = client.simulate_get("/signs/transliteration/$$$")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Invalid transliteration" in result.json["description"]

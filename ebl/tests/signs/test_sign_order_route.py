import falcon


def test_get_signs_by_order(client, sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(f"/signs/{signs[0].name}/neo_assyrian_onset")

    assert result.status == falcon.HTTP_OK
    assert isinstance(result.json, list)


def test_get_signs_by_unknown_order(client) -> None:
    result = client.simulate_get("/signs/SI/not_existing_era")

    assert result.status == falcon.HTTP_OK
    assert result.json == []

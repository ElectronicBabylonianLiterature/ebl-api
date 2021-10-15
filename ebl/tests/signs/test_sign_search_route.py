import falcon
import pytest

from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.domain.sign import Sign, SignName


def test_signs_get(client, sign_repository):
    sign = Sign(SignName("test"))
    sign_repository.create(sign)
    result = client.simulate_get(f"/signs/{sign.name}")

    assert result.json == SignDtoSchema().dump(sign)
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_signs_not_found(client):
    result = client.simulate_get('/words/not found')

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {"listsName": "ABZ", "listsNumber": "377n1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "LaBaSi": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": ":", "subIndex": "1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "LaBaSi": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": ":", "isIncludeHomophones": "true", "subIndex": "2"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "LaBaSi": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": "ku", "subIndex": "1", "isComposite": "true"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "LaBaSi": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
    ],
)
def test_signs_search_route(params, expected, client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params=params)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == expected


def test_signs_search_route_error(client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params={"signs": "P₂"})
    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"

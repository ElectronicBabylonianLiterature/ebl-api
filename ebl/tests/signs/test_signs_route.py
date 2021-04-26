import falcon
import pytest

from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {"listsName": "ABZ", "listsNumber": "377n1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": None,
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
                    "mesZl": None,
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": "bu", "isIncludeHomophones": "true", "subIndex": "1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": None,
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
                    "mesZl": None,
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
    ],
)
def test_include_homophones(params, expected, client, sign_repository, signs):
    signs_repo = MemoizingSignRepository(sign_repository)
    [signs_repo.create(sign) for sign in signs]
    get_result = client.simulate_get("/signs", params=params)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == expected

import falcon
import pytest

from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {"value": ":", "isIncludeHomophones": "false", "isComposite": "false"},
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
            {"value": ":", "isIncludeHomophones": "true", "isComposite": "false"},
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
            {"value": "ku", "isIncludeHomophones": "false", "isComposite": "true"},
            [
                {
                    "lists": [{"name": "KWU", "number": "869"}],
                    "logograms": [],
                    "mesZl": None,
                    "name": "KU",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": "ku"}],
                },
                {
                    "lists": [],
                    "logograms": [],
                    "mesZl": None,
                    "name": "BA",
                    "unicode": [],
                    "values": [
                        {"subIndex": 1, "value": "ba"},
                        {"subIndex": 1, "value": "ku"},
                    ],
                },
            ],
        ),
    ],
)
def test_include_homophones(params, expected, client, sign_repository, signs):
    signs_repo = MemoizingSignRepository(sign_repository)
    [signs_repo.create(sign) for sign in signs]
    get_result = client.simulate_get(f"/signs", params=params)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == expected

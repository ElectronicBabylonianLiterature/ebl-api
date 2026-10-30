from typing import cast

import falcon
import pytest
from bson import BSON, ObjectId
from falcon import testing
from pymongo.database import Database

from ebl.common.domain.stage import Stage
from ebl.common.query.parameter_parser import MAX_QUERY_LIMIT


@pytest.fixture
def many_chapter_rows(database: Database) -> None:
    database["chapters"].insert_many(
        [
            {
                "_id": ObjectId(),
                "textId": {"genre": "L", "category": 1, "index": 1},
                "stage": Stage.STANDARD_BABYLONIAN.long_name,
                "name": str(index),
            }
            for index in range(237)
        ]
    )


def test_large_corpus_query_uses_bounded_pages(
    client: testing.TestClient, many_chapter_rows: None
) -> None:
    response = client.simulate_get(
        "/corpus/query", params={"limit": str(MAX_QUERY_LIMIT + 1), "offset": "0"}
    )
    assert response.status == falcon.HTTP_OK
    payload = cast(dict, cast(testing.Result, response).json)
    assert payload["totalChapters"] == 237
    assert payload["matchCountTotal"] == 0
    assert payload["hasNextPage"] is True
    assert payload["isMatchCountTotalExact"] is True
    assert len(payload["items"]) == MAX_QUERY_LIMIT
    assert "totalDocuments" not in payload


def test_offset_only_corpus_request_defaults_to_fifty(
    client: testing.TestClient, many_chapter_rows: None
) -> None:
    response = client.simulate_get("/corpus/query", params={"offset": "50"})
    assert response.status == falcon.HTTP_OK
    payload = cast(dict, cast(testing.Result, response).json)
    assert payload["totalChapters"] == 237
    assert payload["hasNextPage"] is True
    assert [item["name"] for item in payload["items"]] == [
        str(index) for index in range(50, 100)
    ]
    assert len(BSON.encode(payload)) < 15000


def test_last_and_beyond_last_pages_retain_totals(
    client: testing.TestClient, many_chapter_rows: None
) -> None:
    for offset, expected_size in [(235, 2), (237, 0), (999, 0), (2**63 - 1, 0)]:
        response = client.simulate_get(
            "/corpus/query", params={"limit": "5", "offset": str(offset)}
        )
        assert response.status == falcon.HTTP_OK
        payload = cast(dict, cast(testing.Result, response).json)
        assert payload["totalChapters"] == 237
        assert payload["hasNextPage"] is False
        assert len(payload["items"]) == expected_size


@pytest.mark.parametrize(
    "parameters",
    [
        {"limit": "0"},
        {"limit": "-1"},
        {"limit": "bad"},
        {"limit": "1.5"},
        {"limit": ""},
        {"limit": ["1", "2"]},
        {"offset": "-1"},
        {"offset": "bad"},
        {"offset": "1.5"},
        {"offset": ""},
        {"offset": ["0", "1"]},
        {"offset": str(2**63)},
    ],
)
def test_invalid_corpus_pagination_returns_data_error(
    client: testing.TestClient, parameters: dict
) -> None:
    response = client.simulate_get("/corpus/query", params=parameters)
    assert response.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_no_pagination_arguments_keep_legacy_response_shape(
    client: testing.TestClient, many_chapter_rows: None
) -> None:
    response = client.simulate_get("/corpus/query", params={"legacyFilter": "ignored"})
    assert response.status == falcon.HTTP_OK
    payload = cast(dict, cast(testing.Result, response).json)
    assert set(payload) == {"items", "matchCountTotal"}
    assert len(payload["items"]) == 237


def test_empty_query_keeps_legacy_empty_response(
    client: testing.TestClient, many_chapter_rows: None
) -> None:
    response = client.simulate_get("/corpus/query")
    assert response.status == falcon.HTTP_OK
    payload = cast(dict, cast(testing.Result, response).json)
    assert payload == {"items": [], "matchCountTotal": 0}


def test_equal_collation_names_are_stable_for_paginated_browsing(
    database: Database, client: testing.TestClient
) -> None:
    names = ["I.", "I", "I-"]
    for name in names:
        database["chapters"].insert_one(
            {
                "textId": {"genre": "L", "category": 1, "index": 1},
                "stage": "Standard Babylonian",
                "name": name,
            }
        )
    observed = [
        cast(
            dict,
            cast(
                testing.Result,
                client.simulate_get(
                    "/corpus/query", params={"limit": "1", "offset": str(offset)}
                ),
            ).json,
        )["items"][0]["name"]
        for offset in range(3)
    ]
    assert observed == ["I", "I-", "I."]

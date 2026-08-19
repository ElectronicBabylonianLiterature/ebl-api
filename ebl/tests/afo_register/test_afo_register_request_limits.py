import falcon
import json
import pytest
from falcon import Request
from falcon.testing import create_environ

from ebl.afo_register.web.afo_register_records import (
    MAX_QUERY_BYTES,
    MAX_REQUEST_BYTES,
    validate_request_size,
    validate_texts_and_numbers_query,
)
from ebl.errors import DataError


def build_request_without_content_length(body: str) -> Request:
    environ = create_environ(body=body)
    del environ["CONTENT_LENGTH"]
    return Request(environ)


CUNEIFORM_SIGN = "\U00012000"
CUNEIFORM_SIGN_BYTES = 4


def build_wide_query(byte_length: int) -> str:
    return CUNEIFORM_SIGN * (byte_length // CUNEIFORM_SIGN_BYTES)


def test_validate_query_counts_utf8_bytes_not_code_points():
    query = build_wide_query(MAX_QUERY_BYTES + CUNEIFORM_SIGN_BYTES)

    assert len(query) <= MAX_QUERY_BYTES
    assert len(query.encode("utf-8")) > MAX_QUERY_BYTES
    with pytest.raises(DataError, match=f"at most {MAX_QUERY_BYTES} bytes"):
        validate_texts_and_numbers_query([query])


def test_validate_query_accepts_a_query_at_the_byte_limit():
    query = build_wide_query(MAX_QUERY_BYTES)

    assert len(query.encode("utf-8")) == MAX_QUERY_BYTES
    assert validate_texts_and_numbers_query([query]) == [query]


def test_validate_request_size_accepts_a_body_at_the_limit():
    assert validate_request_size(MAX_REQUEST_BYTES) is None


def test_validate_request_size_accepts_an_unknown_length():
    assert validate_request_size(None) is None


def test_validate_request_size_rejects_an_oversized_body():
    with pytest.raises(DataError, match="Request too large"):
        validate_request_size(MAX_REQUEST_BYTES + 1)


def test_search_by_texts_and_numbers_route_rejects_wide_utf8_query(client) -> None:
    query = build_wide_query(MAX_QUERY_BYTES + CUNEIFORM_SIGN_BYTES)

    result = client.simulate_post(
        "/afo-register/texts-numbers", body=json.dumps([query])
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert (
        result.json["description"]
        == f"Query too long: at most {MAX_QUERY_BYTES} bytes allowed."
    )


def test_a_body_without_content_length_is_never_read():
    body = "x" * (MAX_REQUEST_BYTES * 2)
    request = build_request_without_content_length(body)

    assert len(body.encode("utf-8")) == MAX_REQUEST_BYTES * 2
    assert request.content_length is None
    assert request.bounded_stream.read(MAX_REQUEST_BYTES * 2) == b""


def test_a_body_is_never_read_beyond_its_content_length():
    environ = create_environ(body="x" * (MAX_REQUEST_BYTES * 2))
    environ["CONTENT_LENGTH"] = "100"

    assert len(Request(environ).bounded_stream.read(MAX_REQUEST_BYTES * 2)) == 100


def test_search_by_texts_and_numbers_route_rejects_oversized_content_length(
    client,
) -> None:
    result = client.simulate_post(
        "/afo-register/texts-numbers",
        body=json.dumps(["A B"]),
        headers={"Content-Length": str(MAX_REQUEST_BYTES + 1)},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert result.json["description"].startswith("Request too large")

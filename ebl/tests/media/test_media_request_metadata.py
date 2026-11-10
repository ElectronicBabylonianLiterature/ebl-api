import falcon
import pytest
from falcon import testing

from ebl.errors import DataError
from ebl.media.web.request_metadata import bounded_json_body


def request(body: bytes) -> falcon.Request:
    return testing.create_req(
        method="PATCH", body=body, headers={"Content-Type": "application/json"}
    )


def test_accepts_bounded_object() -> None:
    assert bounded_json_body(request(b'{"caption": "Obverse"}')) == {
        "caption": "Obverse"
    }


@pytest.mark.parametrize("body", [b"{", b"\xff"])
def test_rejects_invalid_json_as_data_error(body: bytes) -> None:
    with pytest.raises(DataError, match="Invalid JSON metadata"):
        bounded_json_body(request(body))


@pytest.mark.parametrize(
    "body",
    [
        # Within the 16 KiB bound; whether the decoder exceeds its recursion
        # limit or parses a non-object depends on the interpreter, but either
        # way the request is rejected as invalid data (422), never a 500.
        b"[" * 16000,
        b"[" * 8000 + b"]" * 8000,
    ],
    ids=["unbalanced", "balanced"],
)
def test_rejects_deeply_nested_json_as_data_error(body: bytes) -> None:
    assert len(body) <= 16384
    with pytest.raises(DataError):
        bounded_json_body(request(body))


def test_rejects_oversize_body() -> None:
    with pytest.raises(falcon.HTTPPayloadTooLarge):
        bounded_json_body(request(b" " * 16385))

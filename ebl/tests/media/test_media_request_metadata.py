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


@pytest.mark.parametrize(
    "body",
    [
        b"{",
        b"\xff",
        # Within the 16 KiB bound, but deeper than the decoder's recursion limit.
        b"[" * 16000,
        b"[" * 8000 + b"]" * 8000,
    ],
)
def test_rejects_invalid_or_deeply_nested_json_as_data_error(body: bytes) -> None:
    assert len(body) <= 16384
    with pytest.raises(DataError, match="Invalid JSON metadata"):
        bounded_json_body(request(body))


def test_rejects_oversize_body() -> None:
    with pytest.raises(falcon.HTTPPayloadTooLarge):
        bounded_json_body(request(b" " * 16385))
